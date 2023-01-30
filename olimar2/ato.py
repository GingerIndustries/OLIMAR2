from contextlib import closing
from io import BytesIO
from dataclasses import dataclass, field, InitVar
from enum import Enum

from websocket import create_connection #upm package(websocket-client)
from websocket._abnf import ABNF #upm package(websocket-client)
import msgpack

class ATOException(Exception):
    def __init__(self, code, message):
        super().__init__(code, message)
        self.code = code
        self.message = message

class StatusType(Enum):
    EXITED = "exited"
    KILLED = "killed"
    CORE_DUMPED = "core_dumped"
    UNKNOWN = "unknown"
    TIMED_OUT = "timed_out"
@dataclass(repr = True)
class Status:
    type: StatusType
    code: int

@dataclass(repr = True)
class Result:
    stdout: BytesIO
    stderr: BytesIO
    stdout_truncated: bool
    stderr_truncated: bool
    status: Status = field(init = False)
    status_type: InitVar[str]
    status_value: InitVar[int]
    timed_out: InitVar[bool]
    real: int
    kernel: int
    user: int
    max_mem: int
    waits: int
    preemptions: int
    major_page_faults: int
    minor_page_faults: int
    input_ops: int
    output_ops: int

    def __post_init__(self, status_type: str, status_value: int, timed_out: bool):
        if timed_out:
            self.status = Status(StatusType.TIMED_OUT, status_value)
        else:
            self.status = Status(StatusType(status_type), status_value)
    

class ATO:
    def __init__(self, address = "wss://ato.pxeger.com/api/v1/ws/execute"):
        self.address = address

    def run(self, language: str, code: str, input: str = "", timeout: int = 10):
        with closing(create_connection(
            self.address,
            headers = ["User-Agent: OLIMAR2"]
        )) as socket:
            socket.send(msgpack.dumps({
                "language": language,
                "code": code,
                "input": input,
                "options": [],
                "arguments": [],
                "timeout": timeout
            }), opcode = ABNF.OPCODE_BINARY)
            stdout = BytesIO()
            stderr = BytesIO()
            while True:
                opcode, data = socket.recv_data()
                if opcode == 8:
                    error = int.from_bytes(data[:2], "big")
                    raise ATOException(error, data[2:])
                data = msgpack.loads(data)
                if "Done" in data.keys():
                    stdout.seek(0)
                    stderr.seek(0)
                    return Result(stdout.read(), stderr.read(), **data["Done"])
                elif "Stdout" in data.keys():
                    stdout.write(data["Stdout"])
                elif "Stderr" in data.keys():
                    stderr.write(data["Stderr"])
                else:
                    raise RuntimeError("Unknown key type", data)
            
            