# import sys
# sys.path.append('../libs')
from psychopy import visual, sound, data, event, core, gui
from psychopy import prefs
prefs.hardware['audioLib']= [
                                'ptb',
                                'sounddevice',
                                'pyo',
                                'pygame'
                            ]
import pandas as pd
from datetime import datetime
import csv
import os
import codecs
import gc

class Experiment:
    def __init__(self, subject=None, age=None, sex=None, block_num=None, block=None):
        self.subject = subject
        self.age = age
        self.sex = sex
        self.block_num = block_num
        self.block = block
        self.system_id = 0
        self.accept = 'space'
        self.win = visual.Window(fullscr=True, color='black', units='pix', screen=self.system_id)
        self.text = visual.TextStim(self.win, text=None, alignText="center", color='white', wrapWidth=700, height=26)


    def create_trials(self):
        trial_list = []

        if self.block == 'practice':
            df = pd.read_csv('./practice_trials.csv', dtype={'condition': str})
        else:
            df = pd.read_csv(f'./trials.csv', dtype={'condition': str})
            df = df[df['block'] == self.block]

        df = df.sample(frac=1).reset_index()    # shuffle row order
        for index, row in df.iterrows():
            trial_dict = row.to_dict()  # need to provide list of dicts to PsychoPy TrialHandler
            trial_dict['date'] = datetime.now()
            trial_dict['subject'] = self.subject
            trial_dict['age'] = self.age
            trial_dict['sex'] = self.sex
            trial_dict['trial_num'] = index+1
            trial_dict['block_num'] = self.block_num
            trial_dict['block'] = self.block
            trial_list.append(trial_dict)

        trials = data.TrialHandler(trialList=trial_list, nReps=1, method='sequential')
        trials.data.addDataType('response')

        return trials
    

    def show_text_and_wait(self, file_name = None, message = None):
        event.clearEvents()
        if message is None:
            with codecs.open (file_name, "r", "utf-8") as file :
                message = file.read()
        self.text.setText(message)
        self.text.draw()
        self.win.flip()
        while True :
            if len(event.getKeys()) > 0:
                core.wait(0.2)
                break
            event.clearEvents()
            core.wait(0.2)
            self.text.draw()
            self.win.flip()


    def make_stim(self, trial):
        mov = visual.MovieStim(
            self.win, 
            trial['video_path'],
            size=[1920, 1200],              
            pos=[0, 0],             
            flipVert=False,         
            flipHoriz=False,        
            loop=False,             
            noAudio=True
        )
        mov_aud = sound.Sound(trial['audio_path'])

        return mov, mov_aud
    

    def rate_confidence(self, trials, scale, responded):
        resp = ''
        if scale.noResponse:
            self.text.setText("A quel point êtes-vous d’accord avec le fait que cette interaction est authentique ? \n \n (gauche: <- ; droite: -> ; confirmer: Espace)")
            self.text.draw()
            scale.draw()
            self.win.flip()
        else:
            resp = scale.getRating()
            trials.addData('response', resp)
            scale.draw()
            self.win.flip()
            responded = True

        return responded, resp
    

    def write_trial(self, res_file, trial, rating):
        row = ['date', 'subject', 'age', 'sex', 'trial_num', 'block_num', 'block', 'video_path', 'audio_path', 'condition', 'category', 'duration', 
                'eye_fit', 'mouth_fit', 'genuineness', 'response']
        
        with open(res_file, 'a', newline='') as file:
                fileWriter = csv.writer(file, dialect='excel')
                if os.stat(res_file).st_size == 0: # if file is empty, insert header
                    fileWriter.writerow(row)
                fileWriter.writerow([trial[i] for i in row[:-1]]+[rating])


    def run(self):
        trials = self.create_trials()
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        res_file = f'./responses/{self.subject}/{timestamp}_{self.subject}_{self.block}.csv'

        if self.block_num == 0:
            for i in range(1, 3):
                self.show_text_and_wait(file_name=f'./instructions/instructions_{i}.txt')
            self.show_text_and_wait(file_name='./instructions/practice.txt')
        # else:
        #     self.show_text_and_wait(file_name=f'./instructions/block_{self.block_num}.txt')
        
        for trial in trials:
            scale = visual.RatingScale(
                                        self.win, 
                                        low=1, 
                                        high=10, 
                                        markerStart=5, 
                                        scale=None,
                                        tickHeight=0.75,
                                        marker='triangle',
                                        textSize=0.5,
                                        labels=['Pas du tout d’accord', 'Complètement d’accord'], 
                                        leftKeys=['left'], 
                                        rightKeys=['right'], 
                                        acceptKeys=[self.accept],
                                        acceptPreText=''
                                    )

            # Trial
            mov, aud = self.make_stim(trial)
            mov.play()
            aud.play()         
            while mov.isFinished == False:
                mov.draw()
                self.win.flip()
            
            # Booleans to track if participant has responded or not
            responded_likert = False
            # Do not move forward until participant has responded to the task
            while responded_likert == False:
                responded, rating = self.rate_confidence(trials, scale, responded_likert)
                responded_likert = responded

            self.write_trial(res_file, trial, rating)

            if trials.getFutureTrial(n=1) != None:
                self.show_text_and_wait(file_name="./instructions/trial_end.txt")
            else:
                if (self.block == 'practice'):
                    self.show_text_and_wait(file_name="./instructions/practice_end.txt")
                elif (self.block_num != 4):
                    self.show_text_and_wait(file_name=f"./instructions/block_{self.block_num}_end.txt")
                elif (self.block_num == 4):
                    self.show_text_and_wait(file_name="./instructions/end.txt")
           
            del scale
            del mov
            del aud
            del trial
            gc.collect()

        self.win.close()
    

if __name__ == '__main__':

    blocks = ['practice', 'eyes', 'mouth', 'nods', 'original']

    subject_info = {u'Subject':'', u'Age':'', u'Sex': u'f/m'}
    dlg = gui.DlgFromDict(subject_info, title=u'Speed Dating - Causal')
    if dlg.OK:
        subject = subject_info[u'Subject']
        age = subject_info[u'Age']
        sex = subject_info[u'Sex']
    else:
        core.quit() #the user hit cancel so exit

    for i in range(len(blocks)):
        block = Experiment(subject=subject, age=age, sex=sex, block_num=i, block=blocks[i])
        block.run()