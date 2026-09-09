// Deterministic keyboard scenario for PinMAME's built-in STTNG six-ball simulator.
#include "libpinmame.h"
#include <atomic>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <thread>
#include <string>

static std::atomic<double> emutime{0};
static std::string output;
static FILE *events;
static bool pulse(double t, double start, double width=.2) { return t>=start && t<start+width; }
static int audio_available(PinmameAudioInfo *info, void*) { return info->samplesPerFrame; }
static int audio_updated(void*, int samples, void*) { emutime=emutime.load()+samples/44100.; return samples; }
static void logger(PINMAME_LOG_LEVEL, const char *fmt, va_list args, void*) { vfprintf(stdout,fmt,args); }
static void state(int s, void*) { fprintf(stdout,"STATE %d\n",s); fflush(stdout); }
static int key(PINMAME_KEYCODE code, void*) {
 double t=emutime.load();
 if (code==PINMAME_KEYCODE_NUMBER_5) return pulse(t,15)||pulse(t,17)||pulse(t,19)||pulse(t,21);
 if (code==PINMAME_KEYCODE_NUMBER_1) return pulse(t,25,1)||pulse(t,40,1);
 if (code==PINMAME_KEYCODE_SPACE) return t>28 && std::fmod(t,4)<.3;
 if (t<45) return 0;
 const PINMAME_KEYCODE sequence[]={PINMAME_KEYCODE_R,PINMAME_KEYCODE_N,PINMAME_KEYCODE_M,PINMAME_KEYCODE_COMMA,PINMAME_KEYCODE_A,PINMAME_KEYCODE_S,PINMAME_KEYCODE_D,PINMAME_KEYCODE_F,PINMAME_KEYCODE_G,PINMAME_KEYCODE_H,PINMAME_KEYCODE_J,PINMAME_KEYCODE_K,PINMAME_KEYCODE_L,PINMAME_KEYCODE_W,PINMAME_KEYCODE_SLASH,PINMAME_KEYCODE_PERIOD,PINMAME_KEYCODE_Z,PINMAME_KEYCODE_X,PINMAME_KEYCODE_C,PINMAME_KEYCODE_V,PINMAME_KEYCODE_B,PINMAME_KEYCODE_E,PINMAME_KEYCODE_MINUS,PINMAME_KEYCODE_I,PINMAME_KEYCODE_O,PINMAME_KEYCODE_Q};
 int slot=int((t-45)/3);
 if (code==PINMAME_KEYCODE_LEFT_CONTROL) return slot%2==0;
 if (code==PINMAME_KEYCODE_RIGHT_CONTROL) return slot%2==1;
 return code==sequence[slot%26] && std::fmod(t-45,3)<.25;
}
static void display(int index, void *data, PinmameDisplayLayout *layout, void*) {
 static int last=-1;
 int t=int(emutime.load());
 if (index || layout->width!=128 || layout->height!=32 || t==last || t%5) return;
 last=t;
 auto path=output+"/dmd-"+std::to_string(t)+".pgm";
 FILE *f=fopen(path.c_str(),"wb"); if(!f)return;
 fprintf(f,"P5\n128 32\n255\n");
 auto pixels=static_cast<unsigned char*>(data);
 for(int i=0;i<4096;++i) { unsigned char b=pixels[i]; fwrite(&b,1,1,f); }
 fclose(f);
}
static void solenoid(PinmameSolenoidState *s, void*) { fprintf(events,"%.6f,%d,%d\n",emutime.load(),s->solNo,s->state); }
int main(int argc,char **argv) {
 if(argc!=4){fprintf(stderr,"usage: play ROM_PARENT OUTPUT_DIR SECONDS\n");return 2;}
 output=argv[2];double duration=std::stod(argv[3]);
 events=fopen((output+"/solenoids.csv").c_str(),"w");if(!events)return 2;
 fprintf(events,"audio_time,solenoid,state\n");
 PinmameConfig config={PINMAME_AUDIO_FORMAT_INT16,44100,"",state,nullptr,display,audio_available,audio_updated,nullptr,nullptr,solenoid,nullptr,key,logger,nullptr};
 snprintf(const_cast<char*>(config.vpmPath),PINMAME_MAX_PATH,"%s/",argv[2]);
 PinmameSetConfig(&config);
 PinmameSetPath(PINMAME_FILE_TYPE_ROMS,argv[1]);
 PinmameSetPath(PINMAME_FILE_TYPE_NVRAM,(output+"/nvram").c_str());
 PinmameSetPath(PINMAME_FILE_TYPE_CONFIG,(output+"/cfg").c_str());
 PinmameSetHandleKeyboard(1);PinmameSetHandleMechanics(0xff);PinmameSetDmdMode(PINMAME_DMD_MODE_BRIGHTNESS);
 if(PinmameRun("sttng_l7")!=PINMAME_STATUS_OK)return 1;
 auto start=std::chrono::steady_clock::now();
 bool reset=false;
 while(emutime<duration){
  std::this_thread::sleep_for(std::chrono::milliseconds(50));
  if(!reset && emutime>=8) { reset=true; PinmameReset(); fprintf(stdout,"RESET after NVRAM initialization\n"); }
  if(std::chrono::steady_clock::now()-start>std::chrono::seconds(int(duration*3+60))) {PinmameStop();fclose(events);return 1;}
 }
 PinmameStop();fclose(events);printf("COMPLETED audio_time=%.3f\n",emutime.load());return 0;
}
