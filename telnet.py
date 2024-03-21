import socket
import ssl

class URL:
    def __init__(self, url):
        self.scheme, url = url.split("://", 1)
        assert self.scheme in ["http", "https", "file"]
        if self.scheme == "http":
            self.port = 80
        elif self.scheme == "https":
            self.port = 443
        elif self.scheme == "file":
            self.filename = url
        if "/" not in url:
            url = url + "/"
        self.host, url = url.split("/", 1)
        self.path = "/" + url
        if ":" in self.host:
            self.host, port = self.host.split(":", 1)
            self.port = int(port)

    def request(self):
        headers = {
            "Host": self.host,
            "Connection": "close",
            "User-Agent": "ChelseaBrowser/1.0"
        }

        s = socket.socket(
            family=socket.AF_INET,
            type=socket.SOCK_STREAM,
            proto=socket.IPPROTO_TCP,
        )
        s.connect((self.host, self.port))

        if self.scheme == "https":
            ctx = ssl.create_default_context()
            s = ctx.wrap_socket(s, server_hostname=self.host)

        # Construct request string with headers
        request_string = "GET {} HTTP/1.1\r\n".format(self.path)
        for header, value in headers.items():
            request_string += "{}: {}\r\n".format(header, value)
        request_string += "\r\n"

        s.send(request_string.encode("utf8"))
    
        response = s.makefile("r", encoding="utf8", newline="\r\n")
        statusline = response.readline()
        version, status, explanation = statusline.split(" ", 2)
        response_headers = {}
        while True:
            line = response.readline()
            if line == "\r\n": break
            header, value = line.split(":", 1)
            response_headers[header.casefold()] = value.strip()
        assert "transfer-encoding" not in response_headers
        assert "content-encoding" not in response_headers
        body = response.read()
        s.close()
        return body

def show(body):
    in_tag = False
    for c in body:
        if c == "<":
            in_tag = True
        elif c == ">":
            in_tag = False
        elif not in_tag:
            print(c, end="")

def ShowFile(url):
    if isinstance(url, str) :
        filename = url
    else:
        slash, filename = url.filename.split("/", 1)
    
    try:
        with open(filename, "r") as file_object:
            contents = file_object.read()
            print(contents)
    except FileNotFoundError:
        print(f"Error: File '{url.filename}' not found.")

def load(url):
    if url.scheme == "file":
        ShowFile(url)
    else:
        body = url.request()
        show(body)
    
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        load(URL(sys.argv[1]))
    else:
        ShowFile("test.txt")