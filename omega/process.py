"""Bounded POSIX subprocess capture. No shell and no disk-backed log spool."""
import os
import selectors
import signal
import subprocess
import time


def execute(argv, cwd, timeout=120, capture_bytes=16000, max_output_bytes=1048576, env=None):
    if (not isinstance(argv,list) or not argv or
            any(not isinstance(x,str) or not x or '\0' in x for x in argv)):
        raise ValueError('Command must be a nonempty argv of nonempty strings')
    if (isinstance(timeout,bool) or not isinstance(timeout,(int,float)) or not 0 < timeout <= 1800 or
            type(capture_bytes) is not int or not 1 <= capture_bytes <= 1048576 or
            type(max_output_bytes) is not int or not capture_bytes <= max_output_bytes <= 16777216):
        raise ValueError('Invalid subprocess bounds')
    started=time.monotonic()
    result={'command':argv,'exit_code':127,'seconds':0.0,'output':'','truncated':False,
            'output_tail':'','timed_out':False,'output_limit_exceeded':False,'total_output_bytes':0,'invalid_utf8':False}
    try:
        proc=subprocess.Popen(argv,cwd=cwd,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT,start_new_session=True,env=env)
    except OSError as exc:
        result.update(output=f'Unable to start command: {exc.strerror}',seconds=round(time.monotonic()-started,3))
        return result
    captured=bytearray()
    tail=bytearray()
    forced=None
    deadline=started+timeout

    def kill_group():
        try:os.killpg(proc.pid,signal.SIGKILL)
        except ProcessLookupError:pass

    try:
        with selectors.DefaultSelector() as selector:
            selector.register(proc.stdout,selectors.EVENT_READ)
            while selector.get_map():
                left=deadline-time.monotonic()
                if left<=0:
                    result['timed_out']=True;forced=124;kill_group();break
                for key,_ in selector.select(min(left,0.05)):
                    chunk=os.read(key.fd,65536)
                    if not chunk:
                        selector.unregister(key.fileobj)
                        continue
                    result['total_output_bytes']+=len(chunk)
                    tail.extend(chunk);del tail[:-min(capture_bytes,4096)]
                    captured.extend(chunk[:max(0,capture_bytes-len(captured))])
                    if result['total_output_bytes']>max_output_bytes:
                        result['output_limit_exceeded']=True;forced=125;kill_group();break
                if forced is not None:break
        if forced is None:
            try:proc.wait(timeout=max(0.001,deadline-time.monotonic()))
            except subprocess.TimeoutExpired:
                result['timed_out']=True;forced=124;kill_group()
        proc.wait()
    finally:
        if proc.poll() is None:kill_group();proc.wait()
        proc.stdout.close()
    try:result['output']=captured.decode('utf-8')
    except UnicodeDecodeError:
        result['output']=captured.decode('utf-8',errors='replace');result['invalid_utf8']=True
    if result['total_output_bytes']>capture_bytes:
        result['output_tail']=tail.decode('utf-8',errors='replace')
    result.update(exit_code=forced if forced is not None else proc.returncode,
                  seconds=round(time.monotonic()-started,3),
                  truncated=result['total_output_bytes']>capture_bytes)
    return result
