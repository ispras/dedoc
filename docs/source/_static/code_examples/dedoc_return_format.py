import json

import requests

filename = "test_dir/example_return_format.docx"


def basic_example() -> dict:
    with open(filename, "rb") as file:
        files = {"file": (filename, file)}
        r = requests.post("http://localhost:1231/upload", files=files, data=dict())
        result = r.content.decode("utf-8")

    assert r.status_code == 200
    return json.loads(result)


def linear_structure_type_example() -> dict:
    with open(filename, "rb") as file:
        files = {"file": (filename, file)}
        r = requests.post("http://localhost:1231/upload", files=files, data=dict(structure_type="linear"))
        result = r.content.decode("utf-8")

    assert r.status_code == 200
    return json.loads(result)


def with_attachments_example() -> dict:
    with open(filename, "rb") as file:
        files = {"file": (filename, file)}
        r = requests.post("http://localhost:1231/upload", files=files, data=dict(with_attachments="true"))
        result = r.content.decode("utf-8")

    assert r.status_code == 200
    return json.loads(result)


def with_base64_attachments_example() -> dict:
    with open(filename, "rb") as file:
        files = {"file": (filename, file)}
        r = requests.post("http://localhost:1231/upload", files=files, data=dict(with_attachments="true", return_base64="true"))
        result = r.content.decode("utf-8")

    assert r.status_code == 200
    return json.loads(result)


def with_parsed_attachments_example() -> dict:
    with open(filename, "rb") as file:
        files = {"file": (filename, file)}
        r = requests.post("http://localhost:1231/upload", files=files, data=dict(with_attachments="true", need_content_analysis="true"))
        result = r.content.decode("utf-8")

    assert r.status_code == 200
    return json.loads(result)


def article_example() -> dict:
    with open("test_dir/article.pdf", "rb") as file:
        files = {"file": ("article.pdf", file)}
        r = requests.post("http://localhost:1231/upload", files=files, data=dict(document_type="article"))
        result = r.content.decode("utf-8")

    assert r.status_code == 200
    return json.loads(result)


if __name__ == "__main__":
    with open("../json_format_examples/basic_example.json", "w") as f:
        json.dump(basic_example(), f, indent=2, ensure_ascii=False)

    with open("../json_format_examples/linear_structure_type.json", "w") as f:
        json.dump(linear_structure_type_example(), f, indent=2, ensure_ascii=False)

    with open("../json_format_examples/with_attachments.json", "w") as f:
        json.dump(with_attachments_example(), f, indent=2, ensure_ascii=False)

    with open("../json_format_examples/with_base64_attachments.json", "w") as f:
        json.dump(with_base64_attachments_example(), f, indent=2, ensure_ascii=False)

    with open("../json_format_examples/with_parsed_attachments.json", "w") as f:
        json.dump(with_parsed_attachments_example(), f, indent=2, ensure_ascii=False)

    with open("../json_format_examples/article_example.json", "w") as f:
        json.dump(article_example(), f, indent=2, ensure_ascii=False)
