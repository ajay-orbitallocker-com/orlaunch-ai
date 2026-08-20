import tiktoken

ENCODING = tiktoken.get_encoding("cl100k_base")
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100

USER_AGENT = "OrbitalLocker/1.0 (ajay@orbitallocker.com)"
