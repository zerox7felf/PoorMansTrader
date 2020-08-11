class Trader():
    _state = ""
    _state_changed = False
    
    def _process(self, klines):
        pass

    def process(self, klines):
        self._state_changed = False
        self._process(klines)

    # returns state and wheter it has been changed during the last process call
    def get_state(self):
        return (self._state, self._state_changed)

    def _set_state(self, state):
        self._state = state
        self._state_changed = True

class TwoPointTerry(Trader):
    _downward_counter = 0
    _upward_counter = 0
    _got_lowpoint = False
    _lowpoint = None
    _got_highpoint = True
    _highpoint = None
    _last_point = None

    def _process(self, klines):
        if self._last_point == None: # First-time setup
            self._last_point = klines[-1]
        else:
            if klines[-1]["middle"] > self._last_point["middle"]:
                self._downward_counter = 0
                self._upward_counter += 1
            else:
                self._upward_counter = 0
                self._downward_counter += 1

            if self._downward_counter >= 1:
                if self.get_state()[0] == "UPWARD_SLOPE" and self._got_lowpoint:
                    self._set_state("HIGHPOINT_FOUND")
                    self._got_highpoint = True
                    self._highpoint = klines[-1]
                    self._got_lowpoint = False
                else:
                    self._set_state("DOWNWARD_SLOPE")
            elif self._upward_counter >= 2:
                if self.get_state()[0] == "DOWNWARD_SLOPE" and self._got_highpoint:
                    self._set_state("LOWPOINT_FOUND")
                    self._got_highpoint = False
                    self._got_lowpoint = True
                    self._lowpoint = klines[-1]
                else:
                    self._set_state("UPWARD_SLOPE")

            if self._got_lowpoint and klines[-1]["middle"] < self._lowpoint["middle"]*0.9995:
                self._set_state("HIGHPOINT_FOUND")
                self._got_highpoint = True
                self._highpoint = klines[-1]
                self._got_lowpoint = False

            print(self.get_state()[0]+"\t"+str(self._downward_counter)+"\t"+str(self._upward_counter))
            self._last_point = klines[-1]

class TittyToucher(Trader):
    _last_avg = None
    _last_point = None
    _avvikelse = None
    
    def __init__(smoothness, avvikelse):
        self._smoothness = smoothness
        self._avvikelse = avvikelse
          
    def _process(self, klines, screen):
        if self._last_point == None: # First-time setup
            self._last_point = klines[-1]
        if len(klines) >= self._smoothness:
            avg = 0
            for i in range(1,self._smoothness+1):
                avg += klines[-i]

            avg = avg / self._smoothness

            self._last_avg = avg
            
        if (100/(avg/self._last_point))>self._avvikelse
            self._set_state("HIGHPOINT_FOUND")
            
        if (100/(avg/self._last_point))<self._avvikelse
            self._set_state("LOWPOINT_FOUND")
        
        
            
