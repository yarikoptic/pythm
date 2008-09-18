import os
import select
import subprocess
import time
import sys
from threading import Lock

#http://code.activestate.com/recipes/542195/

class MPlayer(object):
    """ A class to access a slave mplayer process
    you may want to use command(name, args*) directly
    or call populate() to access functions (and minimal doc).

    Exemples:
        mp.command('loadfile', '/desktop/funny.mp3')
        mp.command('pause')
        mp.command('quit')

    Note:
        After a .populate() call, you can access an higher level interface:
            mp.loadfile('/desktop/funny.mp3')
            mp.pause()
            mp.quit()

        Beyond syntax, advantages are:
            - completion
            - minimal documentation
            - minimal return type parsing
    """

    exe_name = 'mplayer' if os.sep == '/' else 'mplayer.exe'

    def __init__(self,niceval=None):
        args = [self.exe_name, '-slave', '-quiet', '-idle','-nolirc']
        self._mplayer = subprocess.Popen(args,
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, bufsize=1)
        
        if self._mplayer and niceval!=None:
            pid = self._mplayer.pid
            os.system("renice "+ str(niceval) +" -p "+str(pid))
        
        self.lock = Lock()

    def command(self,cmd,*args):
        """
        a command that does not read anything
        """
        return self._cmd(cmd,None,False,*args)
    
    def arraycmd(self,name,key,*args):
        """
        array reading of mplayers output
        """
        return self._cmd(name,key,True,*args)
            
    def cmd(self,name,key,*args):
        """
        single line reading with key
        """
        return self._cmd(name,key,False,*args)
    
    def quit(self):
        self.command("quit",0)
        self._mplayer.wait()
    
    def _cmd(self,name,key,readall,*args):
        """
        key is the beginning of a line that the command waits for.
        if it is None, the read from mplayers stdout will be omitted.
        if readall is true, all is read until a line begins with key.
        """
        cmd = '%s%s%s\n'%(name,
                ' ' if args else '',
                ' '.join(repr(a) for a in args)
                )        
        
        
        if readall:
            ret = []
        else:
            ret = None
        
        self.lock.acquire()  
        i = 0      
        try:
            #print "CMD: " + str(cmd)
            self._mplayer.stdin.write(cmd)
            if key != None:
                while any(select.select([self._mplayer.stdout.fileno()], [], [], 20)):
                    tmp = self._mplayer.stdout.readline()
                    #print "MPLAYER:" + tmp.strip()
                    if readall:
                        ret.append(tmp)
                        if tmp.startswith(key):
                            break
                    else:
                        
                        if tmp.startswith(key):
                            val = tmp.split('=', 1)[1].rstrip()
                            try:
                                ret = eval(val)
                            except:
                                ret =  val
                            break
        except Exception,e:
            print "error in mplayer.cmd: ", e
            pass
        
        
        self.lock.release()

        return ret
