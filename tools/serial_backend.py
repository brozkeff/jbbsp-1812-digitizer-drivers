# Copyright (c) 2026 Martin brozkeff Malec
# SPDX-License-Identifier: EUPL-1.2
# Licensed under EUPL v. 1.2 only.
"""Small serial transports. Raw I/O only; no tablet protocol knowledge."""
from __future__ import annotations

import array
import copy
import errno
import importlib.util
import os
import select
import time
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Settings:
    port: str
    baud: int = 9600
    bits: int = 8
    parity: str = "N"
    stopbits: int = 1
    dtr: bool = False
    rts: bool = False
    backend: str = "auto"

    def validate(self):
        if not self.port:
            raise ValueError("An explicit serial port is required")
        if self.baud <= 0 or self.bits not in (7, 8):
            raise ValueError("Baud must be positive; data bits must be 7 or 8")
        if self.parity not in ("N", "E", "O") or self.stopbits not in (1, 2):
            raise ValueError("Parity must be N/E/O; stop bits must be 1 or 2")
        if self.backend not in ("auto", "posix", "pyserial"):
            raise ValueError("Unknown serial backend")

    def to_dict(self):
        return asdict(self)


class PosixPort:
    """Exclusive raw POSIX tty, restoring termios before closing.

    Opening a tty can itself affect modem lines. False line defaults do not
    guarantee a glitch-free physical open. Unsupported modem ioctls are reported.
    """
    name = "posix"

    def __init__(self, settings):
        import fcntl
        import termios
        self.fcntl, self.termios = fcntl, termios
        self.fd = None
        self.saved = None
        self.saved_modem = None
        self.settings = settings
        self.line_support = {}
        self.original_lines_restored = False

    def open(self):
        s, t = self.settings, self.termios
        s.validate()
        speed = getattr(t, f"B{s.baud}", None)
        if speed is None:
            raise ValueError(f"POSIX backend has no baud constant for {s.baud}")
        try:
            self.fd = os.open(s.port, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
            if not os.isatty(self.fd):
                raise ValueError("Selected path is not a tty")
            self.fcntl.ioctl(self.fd, t.TIOCEXCL)
            self.saved = t.tcgetattr(self.fd)
            attrs = copy.deepcopy(self.saved)
            attrs[0] = 0  # No translations, stripping, parity markers, or XON/XOFF.
            attrs[1] = 0
            attrs[2] = t.CLOCAL | t.CREAD | (t.CS7 if s.bits == 7 else t.CS8)
            if s.parity != "N":
                attrs[2] |= t.PARENB
                if s.parity == "O":
                    attrs[2] |= t.PARODD
            if s.stopbits == 2:
                attrs[2] |= t.CSTOPB
            attrs[3] = 0  # Raw, no echo, canonical processing, or signal chars.
            attrs[4] = attrs[5] = speed
            attrs[6][t.VMIN] = 0
            attrs[6][t.VTIME] = 0
            t.tcsetattr(self.fd, t.TCSANOW, attrs)
            self.saved_modem = self._modem_bits()
            self.set_lines(s.dtr, s.rts)
            return self
        except BaseException:
            self.close()
            raise

    def _modem_bits(self):
        buf = array.array("i", [0])
        try:
            self.fcntl.ioctl(self.fd, self.termios.TIOCMGET, buf, True)
            return buf[0]
        except OSError as exc:
            if exc.errno in (errno.ENOTTY, errno.EINVAL):
                return None
            raise

    def set_lines(self, dtr, rts):
        t = self.termios
        for name, value, flag in (("dtr", dtr, t.TIOCM_DTR), ("rts", rts, t.TIOCM_RTS)):
            try:
                self.fcntl.ioctl(self.fd, t.TIOCMBIS if value else t.TIOCMBIC,
                                 array.array("i", [flag]))
                self.line_support[name] = True
            except OSError as exc:
                if exc.errno not in (errno.ENOTTY, errno.EINVAL):
                    raise
                self.line_support[name] = False
        return dict(self.line_support)

    def modem_status(self):
        bits = self._modem_bits()
        if bits is None:
            return {"supported": False}
        t = self.termios
        return {"supported": True, **{name: bool(bits & flag) for name, flag in
                (("cts", t.TIOCM_CTS), ("dsr", t.TIOCM_DSR),
                 ("dcd", t.TIOCM_CAR), ("ri", t.TIOCM_RI))}}

    def read(self, timeout):
        ready, _, _ = select.select([self.fd], [], [], timeout)
        if not ready:
            return b""
        try:
            data = os.read(self.fd, 4096)
        except BlockingIOError:
            return b""
        if not data:
            raise OSError(errno.EIO, "Serial endpoint disconnected")
        return data

    def write(self, data):
        remaining = memoryview(data)
        total = 0
        deadline = time.monotonic() + 2.0
        while remaining:
            timeout = deadline - time.monotonic()
            if timeout <= 0 or not select.select([], [self.fd], [], timeout)[1]:
                raise TimeoutError(f"Serial write timed out after {total}/{len(data)} bytes")
            try:
                count = os.write(self.fd, remaining)
            except BlockingIOError:
                continue
            if not count:
                raise OSError("Serial write made no progress")
            total += count
            remaining = remaining[count:]
        return total

    def close(self):
        if self.fd is None:
            return
        errors = []
        try:
            if self.saved_modem is not None:
                try:
                    self.fcntl.ioctl(self.fd, self.termios.TIOCMSET,
                                     array.array("i", [self.saved_modem]))
                    self.original_lines_restored = True
                except OSError as exc:
                    errors.append(str(exc))
            if self.saved is not None:
                try:
                    self.termios.tcsetattr(self.fd, self.termios.TCSANOW, self.saved)
                except OSError as exc:
                    errors.append(str(exc))
        finally:
            try:
                self.fcntl.ioctl(self.fd, self.termios.TIOCNXCL)
            except OSError as exc:
                errors.append(str(exc))
            os.close(self.fd)
            self.fd = None
        return errors


class PySerialPort:
    name = "pyserial"

    def __init__(self, settings):
        import serial
        self.settings = settings
        self.serial = serial.Serial(port=None, baudrate=settings.baud,
                                    bytesize=settings.bits, parity=settings.parity,
                                    stopbits=settings.stopbits, timeout=0.1,
                                    write_timeout=2, xonxoff=False, rtscts=False,
                                    dsrdtr=False, exclusive=True if os.name == "posix" else None)
        self.serial.dtr = settings.dtr
        self.serial.rts = settings.rts
        self.line_support = {"dtr": "requested-unverified", "rts": "requested-unverified"}
        self.original_lines_restored = False

    def open(self):
        self.settings.validate()
        self.serial.port = self.settings.port
        try:
            self.serial.open()
            return self
        except BaseException:
            self.serial.close()
            raise

    def read(self, timeout):
        self.serial.timeout = timeout
        return self.serial.read(max(1, min(self.serial.in_waiting, 4096)))

    def write(self, data):
        count = self.serial.write(data)
        if count != len(data):
            raise OSError(f"Partial serial write: {count}/{len(data)}")
        return count

    def set_lines(self, dtr, rts):
        self.serial.dtr, self.serial.rts = dtr, rts
        return dict(self.line_support)

    def modem_status(self):
        try:
            return {"supported": True, **{key: getattr(self.serial, key)
                    for key in ("cts", "dsr", "cd", "ri")}}
        except OSError as exc:
            return {"supported": False, "reason": str(exc)}

    def close(self):
        self.serial.close()
        return []


def make_port(settings):
    settings.validate()
    backend = settings.backend
    if backend == "auto":
        backend = "pyserial" if importlib.util.find_spec("serial") else "posix"
    if backend == "posix":
        if os.name != "posix":
            raise ValueError("Install pySerial for non-POSIX serial access")
        return PosixPort(settings)
    try:
        return PySerialPort(settings)
    except ImportError as exc:
        raise ValueError("Run uv sync to install the project's pySerial dependency") from exc
