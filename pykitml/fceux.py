import warnings
import socket

class FCEUXServer:
    '''
    Server class for making NES bots. Uses FCEUX emulator.
    Visit https://www.fceux.com for info. You will also need to
    load client lua script in the emulator.
    '''
    def __init__(self, frame_func, quit_func=None, ip='localhost', port=1234):
        '''
        Parameters
        ----------
        frame_func : function
            This function will be called every frame. The function should
            accept two argument, :code:`server` (reference to this class) 
            and :code:`frame` (number of frames executed). 
        quit_func : function
            This function will be executed when the server disconnects from
            the emulator
        ip : str
            IP address of the computer.
        port : int
            Port to listen to.
        '''
        # Eshtablish connection with client
        self._serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._serversocket.bind((ip, port))
        self._serversocket.listen(5)
        self._clientsocket, self._address = self._serversocket.accept()
        
        # This function will be called every frame
        self._on_frame_func = frame_func
        self._on_quit_func = quit_func

        self._server_info = self.recv() + ' ' + str(self._address)
        self.send('ACK')

    @property
    def info(self):
        '''
        Emulator info and lua version.
        '''
        return self._server_info

    def send(self, msg):
        '''
        Send message to lua code running on the emulator.

        Parameters
        ----------
        msg : str
        '''
        if(not type(msg) is str):
            self.quit()
            raise TypeError('Arguments have to be string')

        self._clientsocket.send(bytes(msg+'\n', 'utf-8'))

    def recv(self):
        '''
        Receive message from lua code running on emulator.

        Returns
        -------
        str
            Received message from emulator.
        '''
        return self._clientsocket.recv(4096).decode('utf-8')

    def start(self, *args):
        '''
        Starts the server, waits for emulator to connect.
        Calls :code:`frame_func` every frame after connection
        has been established.

        Parameters
        ----------
        *args
            Argument list containing all the lua code to be
            compiled and executed on the emulator.
        '''
        try:
            for code in args:
                self.compile(code)

            # Keep receiving messaged from FCEUX and acknowledge
            while True:
                # Receive message from client    
                frame_str = self.recv()
                if(len(frame_str) == 0): 
                    self.quit('Client had quit')
                frame = int(frame_str)
                self._on_frame_func(self, frame)
        
        except BrokenPipeError:
            self.quit('Client has quit.')
        except KeyboardInterrupt:
            self.quit()

    def compile(self, code):
        '''
        Compile lua code to be run on the emulator.

        Parameters
        ----------
        code : str
        '''
        def format_code(code):
            lines = code.split('\n')
            non_empty_lines = list(filter(lambda str: len(str)!=0, lines))
            return ';'.join(non_empty_lines)

        code_id = str(id(code))
        code_formatted = format_code(code)
        self.send('CODE')
        self.send(code_id)
        self.send(code_formatted)

    def exec(self, code, *args):
        '''
        Execute compiled code on the emulator.

        Parameters
        ----------
        code : str
        *args
            Arguments to the lua code
        '''
        self.send('EXEC')
        self.send(str(id(code)))
        for str_send in args: self.send(str_send)

    def frame_advance(self):
        '''
        Move to next frame, should be called at the end of 
        :code:`frame_func`.
        '''
        # Send back continue message
        self.send('CONT')

    def get_joypad(self):
        '''
        Returns
        -------
        str
            Joypad button states.
        '''
        self.send('JOYPAD')
        return self.recv()

    def set_joypad(self, up=False, down=False, left=False, 
            right=False, A=False, B=False, start=False, select=False):
        '''
        Set joypad button states.
        '''
        self.send('SETJOYPAD')
        joypad = str(up)+' '+str(down)+' '+str(left)+' '+str(right)\
            +' '+str(A)+' '+str(B)+' '+str(start)+' '+str(select)
        self.send(joypad)

    def quit(self, reason=''):
        '''
        Disconnect from emulator.

        Parameters
        ----------
        reason : str
            Reason for quitting.
        '''
        if(self._on_quit_func is not None):
            self._on_quit_func()
        self._serversocket.close()
        self._clientsocket.close()
        print(reason)
        print('Server has quit.')
        exit()
    
if(__name__ == '__main__'):
    def on_frame(server, frame):
        print(frame)
        print(server.get_joypad())
        server.frame_advance()

    server = FCEUXServer(on_frame)
    print(server.info)
    server.start()

