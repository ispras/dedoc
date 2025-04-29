class Model:
    """
    TensorFlow CNN model(Soon Pytorch) for font's glyphs prediction.
    Used in PDFBrokenEncodingReader.
    """

    def __init__(self):
        from dedoc.readers.pdf_reader.pdf_txtlayer_reader.pdf_broken_encoding_reader.config import Language
        self.model = None
        self.__load_weights()
        s = sorted(Language.Russian_and_English.value, key=lambda i: str(ord(i)))
        self.labels = [ord(i) for i in s]

    def __assert_labels_and_model(self):
        assert self.model.layers[-1].output_shape[-1] == len(self.labels)

    def recognize_glyph(self, images):
        import cv2
        import numpy as np

        images_readen = []
        for png in images:
            stream = open(png, "rb")
            bytes = bytearray(stream.read())
            numpyarray = np.asarray(bytes, dtype=np.uint8)
            img = cv2.imdecode(numpyarray, cv2.IMREAD_UNCHANGED)
            images_readen.append(np.array(img).reshape(28, 28, 1))
            stream.close()

        images_readen = np.array(images_readen)

        probs = self.model.predict(images_readen, verbose=0)
        problabels = probs.argmax(axis=-1)

        predictions = [self.labels[label] for label in problabels]

        return predictions

    def __load_weights(self) -> None:
        import os
        from dedoc.config import get_config
        from keras.models import load_model
        from huggingface_hub import hf_hub_download
        out_dir = get_config()["resources_path"]
        out_name = "rus_eng.h5"
        os.makedirs(out_dir, exist_ok=True)
        real_path = os.path.realpath(hf_hub_download(repo_id=f"sinkudo/tf_cnn", filename=out_name))
        model = load_model(real_path)
        self.model = model
