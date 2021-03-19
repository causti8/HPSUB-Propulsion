def run_animation():
    from time import sleep
    for i in range(10):
        print('.', end='')
        sleep(0.25)
    print('.', end='\r')


class XRotorInterface:

    def __init__(self, verbose=False):
        self.xrotor_path = 'bin\\xrotor.exe'
        self.verbose = verbose
        print('attempting to spawn XROTOR instance from ' + self.xrotor_path)
        self._create_process()

    def __call__(self, command):
        if self.verbose:
            print('sending command: ' + str(command))
        self._send_command(command)

    def finalize(self):
        print('finalizing xrotor interface')
        self._kill_process()

    def _create_process(self):
        raise NotImplementedError

    def _send_command(self, command):
        raise NotImplementedError

    def _kill_process(self):
        raise NotImplementedError


class XRotorSubprocessInterface(XRotorInterface):
    def _create_process(self):
        from subprocess import Popen, PIPE
        self.process = Popen(self.xrotor_path, stdin=PIPE, stdout=PIPE, stderr=PIPE, encoding='utf-8')

    def _send_command(self, command):
        self.process.stdin.write(f'{command}\n')

    def _kill_process(self):
        # the use of threading is because subprocess executes within
        # communicate. it does not spawn multiple threads, simply uses thread
        # functions to determine the execution status of communicate.
        from threading import Thread
        thread = Thread(target=self.process.communicate)
        thread.start()
        while thread.is_alive():
            run_animation()
        print('\n')

