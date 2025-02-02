import socket
import ssl

class URL:
    def __init__(self, url):
        self.view = "web"
        try:
            if isinstance(url, list):
                url = " ".join(url)

            if "view-source" in url:
                self.view, url = url.split(":", 1)
                print(self.view)
                self.scheme, url = url.split("://", 1)

            if "://" in url:
                self.scheme, url = url.split("://", 1)
            elif "," in url:
                self.scheme, self.mimetype = url.split(":", 1)
                url = self.mimetype
            

            assert self.scheme in ["http", "https", "file", "data"]

            if "/" not in url:
                url = url + "/"
            self.host, url = url.split("/", 1)
            self.path = "/" + url

            if self.scheme == "http":
                self.port = 80
            elif self.scheme == "https":
                self.port = 443
            elif self.scheme == "file": 
                self.filename = url
            elif self.scheme == "data":
                self.data_type, self.data_message = url.split(",", 1)

            if ":" in self.host:
                self.host, port = self.host.split(":", 1)
                self.port = int(port)
        except:
            print("Malformed URL found, falling back to the default home page.")
            print("  URL was: " + url)
            self.__init__("file:///test.txt")

    def request(self):
        s = socket.socket(
            family=socket.AF_INET,
            type=socket.SOCK_STREAM,
            proto=socket.IPPROTO_TCP,
        )
        s.connect((self.host, self.port))
    
        if self.scheme == "https":
            ctx = ssl.create_default_context()
            s = ctx.wrap_socket(s, server_hostname=self.host)
    
        s.send(("GET {} HTTP/1.0\r\n".format(self.path) + \
                "Host: {}\r\n\r\n".format(self.host)) \
               .encode("utf8"))
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

    def __repr__(self):
        return "URL(scheme={}, host={}, port={}, path={!r})".format(
            self.scheme, self.host, self.port, self.path)

def show(body):
    in_tag = False
    entity_buffer = ""  # Buffer to store characters for entity decoding

    for c in body:
        if c == "<":  # Start of a tag
            in_tag = True
        elif c == ">":  # End of a tag
            in_tag = False
        elif not in_tag:  # Only print characters outside of tags
            if c == "&":
                in_tag = True
                entity_buffer = ""  # Reset buffer for new entity
            elif c == ";":
                if entity_buffer in ("lt", "gt"):  # Check for known entities
                    if entity_buffer == "lt":
                        print("<", end="")
                elif entity_buffer == "gt":
                    print(">", end="")
                else:
                    print("&" + entity_buffer + ";", end="")  # Print unknown entity as-is
                entity_buffer = ""  # Clear buffer after handling entity
            else:
                entity_buffer += c  # Append characters while processing entity
                print(c, end="")  # Print regular characters
  
    # Handle leftover entity at the end (if any)
    if in_tag:
        print("&" + entity_buffer, end="")


def show_file(filename):
    try:
        with open(filename, "r") as file_objects:
            contents = file_objects.read()
            show(contents)
    except FileNotFoundError:
        print(f"File '{filename}' not found.")

def load(url):
    if url.scheme == "file":
        show_file(url.filename)
    elif url.scheme == "data":
        print(url.data_message)
    else:
        if url.view == "view-source":
            body = url.request()
            print(body)
        else:
            body = url.request()
            show(body)

if __name__ == "__main__":
    import sys
    if "http" in sys.argv[1]:
        load(URL(sys.argv[1]))
    elif len(sys.argv) > 2:
        load(URL(sys.argv[1:]))
    else:
        load(URL("file:///test.txt"))