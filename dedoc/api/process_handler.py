import asyncio
import base64
import logging
import os
import pickle
import signal
import traceback
from multiprocessing import Process, Queue
from typing import Optional
from urllib.request import Request

from anyio import get_cancelled_exc_class

from dedoc.api.cancellation import cancel_on_disconnect
from dedoc.api.schema import ParsedDocument
from dedoc.common.exceptions.dedoc_error import DedocError
from dedoc.config import get_config
from dedoc.dedoc_manager import DedocManager


class ProcessHandler:
    """
    Class for file parsing by DedocManager with support for client disconnection.
    If client disconnects during file parsing, the process of parsing is fully terminated and API is available to receive new connections.

    Handler uses the following algorithm:
    1. Master process is used for checking current connection (client disconnect)
    2. Child process is working on the background and waiting for the input file in the input_queue
    3. Master process calls the child process for parsing and transfers data through the input_queue
    4. Child process is parsing file using DedocManager
    5. The result of parsing is transferred to the master process through the output_queue
    6. If client disconnects, the child process is terminated. The new child process with queues will start with the new request
    """
    def __init__(self, logger: logging.Logger) -> None:
        self.input_queue = Queue()
        self.output_queue = Queue()
        self.logger = logger
        self.process = Process(target=self.__parse_file, args=[self.input_queue, self.output_queue])
        self.process.start()

    async def handle(self, request: Request, parameters: dict, file_path: str, tmpdir: str) -> Optional[ParsedDocument]:
        """
        Handle request in a separate process.
        Checks for client disconnection and terminate the child process if client disconnected.
        """
        if self.process is None:
            self.logger.info("Initialization of a new parsing process")
            self.__init__(logger=self.logger)

        self.logger.info("Putting file to the input queue")
        self.input_queue.put(pickle.dumps((parameters, file_path, tmpdir)), block=True)

        loop = asyncio.get_running_loop()
        async with cancel_on_disconnect(request, self.logger):
            try:
                future = loop.run_in_executor(None, self.output_queue.get)
                result = await future
            except get_cancelled_exc_class():
                self.logger.warning("Terminating the parsing process")
                if self.process is not None:
                    self.process.terminate()
                self.process = None
                future.cancel(DedocError)
                return None

        result = pickle.loads(result)
        if isinstance(result, ParsedDocument):
            self.logger.info("Got the result from the output queue")
            return result

        raise DedocError.from_dict(result)

    def __parse_file(self, input_queue: Queue, output_queue: Queue) -> None:
        """
        Function for file parsing in a separate (child) process.
        It's a background process, i.e. it is waiting for a task in the input queue.
        The result of parsing is returned in the output queue.

        Operations with `signal` are used for saving master process while killing child process.
        See the issue for more details: https://github.com/fastapi/fastapi/issues/1487
        """
        signal.set_wakeup_fd(-1)
        signal.signal(signal.SIGTERM, signal.SIG_DFL)
        signal.signal(signal.SIGINT, signal.SIG_DFL)

        manager = DedocManager(config=get_config())
        manager.logger.info("Parsing process is waiting for the task in the input queue")

        while True:
            file_path = None
            try:
                parameters, file_path, tmp_dir = pickle.loads(input_queue.get(block=True))
                manager.logger.info("Parsing process got task from the input queue")
                return_format = str(parameters.get("return_format", "json")).lower()
                document_tree = manager.parse(file_path, parameters={**dict(parameters), "attachments_dir": tmp_dir})

                if return_format == "html":
                    self.__add_base64_info_to_attachments(document_tree, tmp_dir)

                output_queue.put(pickle.dumps(document_tree.to_api_schema()), block=True)
                manager.logger.info("Parsing process put task to the output queue")
            except DedocError as e:
                tb = traceback.format_exc()
                manager.logger.error(f"Exception {e}: {e.msg_api}\n{tb}")
                output_queue.put(pickle.dumps(e.__dict__), block=True)
            except Exception as e:
                exc_message = f"Exception {e}\n{traceback.format_exc()}"
                filename = "" if file_path is None else os.path.basename(file_path)
                manager.logger.error(exc_message)
                output_queue.put(pickle.dumps({"msg": exc_message, "filename": filename}), block=True)

    def __add_base64_info_to_attachments(self, document_tree: ParsedDocument, attachments_dir: str) -> None:
        for attachment in document_tree.attachments:
            with open(os.path.join(attachments_dir, attachment.metadata.temporary_file_name), "rb") as attachment_file:
                attachment.metadata.add_attribute("base64", base64.b64encode(attachment_file.read()).decode("utf-8"))
