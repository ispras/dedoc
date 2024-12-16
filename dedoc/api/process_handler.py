import asyncio
import base64
import logging
import os
import pickle
import signal
import tempfile
import traceback
from multiprocessing import Process, Queue
from typing import Optional, Union
from urllib.request import Request

from anyio import get_cancelled_exc_class
from fastapi import UploadFile

from dedoc import DedocManager
from dedoc.api.cancellation import cancel_on_disconnect
from dedoc.common.exceptions.dedoc_error import DedocError
from dedoc.config import get_config
from dedoc.data_structures import ParsedDocument
from dedoc.utils.utils import save_upload_file


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

    async def handle(self, request: Request, parameters: dict, file: Union[UploadFile, str]) -> Optional[ParsedDocument]:
        """
        Handle request in a separate process.
        Checks for client disconnection and terminate the child process if client disconnected.
        """
        if not self.process.is_alive():
            self.__init__(logger=self.logger)

        self.logger.info("Putting file to the input queue")
        self.input_queue.put(pickle.dumps((parameters, file)), block=True)

        loop = asyncio.get_running_loop()
        async with cancel_on_disconnect(request, self.logger):
            try:
                future = loop.run_in_executor(None, self.output_queue.get)
                result = await future
            except get_cancelled_exc_class():
                self.logger.warning("Terminating the parsing process")
                self.process.terminate()
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
            try:
                parameters, file = pickle.loads(input_queue.get(block=True))
                manager.logger.info("Parsing process got task from the input queue")
                return_format = str(parameters.get("return_format", "json")).lower()
                with tempfile.TemporaryDirectory() as tmpdir:
                    file_path = file if isinstance(file, str) else save_upload_file(file, tmpdir)
                    document_tree = manager.parse(file_path, parameters={**dict(parameters), "attachments_dir": tmpdir})

                    if return_format == "html":
                        self.__add_base64_info_to_attachments(document_tree, tmpdir)

                output_queue.put(pickle.dumps(document_tree), block=True)
                manager.logger.info("Parsing process put task to the output queue")
            except Exception as e:
                tb = traceback.format_exc()
                manager.logger.error(f"Exception {e}\n{tb}")
                output_queue.put(pickle.dumps(e.__dict__), block=True)

    def __add_base64_info_to_attachments(self, document_tree: ParsedDocument, attachments_dir: str) -> None:
        for attachment in document_tree.attachments:
            with open(os.path.join(attachments_dir, attachment.metadata.temporary_file_name), "rb") as attachment_file:
                attachment.metadata.add_attribute("base64", base64.b64encode(attachment_file.read()).decode("utf-8"))
