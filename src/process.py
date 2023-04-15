import os
import shlex
import signal
import subprocess
import tempfile

#Process(f'xdotool search --all --name {name}').wait().stdout

# with Process(CMD, capture=False):
        
#     p = Process('roslaunch test test.launch')
#     p.wait()
        
class Process:
    """
    Convenience wrapper for subprocess.Popen. Allows to:
    - pass cmd as a string despite not using shell
    - append env variables to spawned process context
    - capture output (stdout, stderr),
    - send SIGINT to spawned process group to stop it
    """

    def __init__(self, cmd, shell=False, env=None, capture=True):
        self.cmd = cmd
        self._rc = None
        self._files = {}
        kw = dict(preexec_fn=os.setsid, shell=shell, close_fds=True)
        if not shell:
            cmd = shlex.split(cmd)
        if env:
            kw.update(env={**os.environ.copy(), **env})
        if capture:
            self._files = dict(
                stdout=tempfile.NamedTemporaryFile(mode="w"),
                stderr=tempfile.NamedTemporaryFile(mode="w"),
                stdin=tempfile.NamedTemporaryFile(mode="r"))
            kw.update(**self._files)
        self._process = subprocess.Popen(cmd, **kw)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.__del__()
        return False

    def __del__(self):
        if not self.done:
            self.kill()
        for f in self._files.values():
            f.close()

    @property
    def pid(self):
        return self._process.pid

    @property
    def returncode(self):
        if self._rc is None:
            self._rc = self._process.poll()
        return self._rc

    @property
    def done(self):
        return self.returncode is not None

    @property
    def stdout(self):
        with open(self._files['stdout'].name) as f:
            return f.read()

    @property
    def stderr(self):
        with open(self._files['stderr'].name) as f:
            return f.read()

    def kill(self):
        if not self.done:
            os.killpg(self.pid, signal.SIGINT)
        return self.wait()

    def wait(self):
        self._process.wait()
        return self
