"""Exercise the actual sketch with host mocks; board compilation is separate."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


@unittest.skipUnless(shutil.which('g++'), 'Host firmware simulation needs g++')
class FirmwareTests(unittest.TestCase):
    def test_soil_warning_button_debounce_and_timed_simulation(self):
        root = Path(__file__).resolve().parents[1]
        harness = r'''
#include <cassert>
#include <sstream>
#include <string>
using byte = unsigned char;
const int HIGH=1, LOW=0, INPUT=0, INPUT_PULLUP=2, OUTPUT=1, A0=14;
unsigned long clockMs=0;
int pins[20]={}, soilRaw=800;
unsigned long millis(){return clockMs;}
void pinMode(int pin,int mode){if(mode==INPUT_PULLUP)pins[pin]=HIGH;}
int digitalRead(int pin){return pins[pin];}
void digitalWrite(int pin,int value){pins[pin]=value;}
int analogRead(int){return soilRaw;}
long map(long x,long a,long b,long c,long d){return (x-a)*(d-c)/(b-a)+c;}
long constrain(long x,long a,long b){return x<a?a:x>b?b:x;}
struct SerialMock {
 std::ostringstream out;
 void begin(int){}
 template<class T> void print(T value){out<<value;}
 template<class T> void println(T value){out<<value<<"\n";}
} Serial;
#include "watering_system.ino"
int main(){
 setup();
 clockMs=100; loop(); assert(pins[7]==HIGH); assert(!simulating);
 pins[4]=LOW; clockMs=110; loop();
 clockMs=130; loop(); assert(!simulating);
 clockMs=151; loop(); assert(simulating); assert(pins[8]==HIGH);
 clockMs=5150; loop(); assert(simulating);
 clockMs=5151; loop(); assert(!simulating); assert(pins[8]==LOW);
 // Holding the button does not trigger a second simulation.
 clockMs=5300; loop(); assert(!simulating); assert(pins[7]==HIGH);
 soilRaw=350; pins[2]=HIGH; pins[3]=LOW;
 clockMs=5400; loop(); assert(pins[7]==LOW);
 auto text=Serial.out.str();
 assert(text.find("\"needs_water\":1")!=std::string::npos);
 assert(text.find("\"watering_simulated\":1")!=std::string::npos);
 assert(text.find("\"motion\":1,\"screen_down\":1")!=std::string::npos);
 assert(text.find("\"soil_percent\":100")!=std::string::npos);
}
'''
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'test.cpp'
            binary = Path(directory) / 'test'
            source.write_text(harness)
            subprocess.run(['g++', '-std=c++11', '-Wall', '-Wextra', '-Werror',
                            '-I', str(root), str(source), '-o', str(binary)], check=True)
            subprocess.run([str(binary)], check=True)
