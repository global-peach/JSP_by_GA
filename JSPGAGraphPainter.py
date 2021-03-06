import numpy as np
import matplotlib.pyplot as plt
from JSPGA import GA

class JSPGAGraphPainter:
    def main(self,Processing_time, Processing_Group, Machine_start_time, Time_efficent, Machine_buffer):
        ga = GA()
        d, Best_fit, Worst_fit, Avg_fit = ga.start(Processing_time, Processing_Group, Machine_start_time, Time_efficent, Machine_buffer)
        self.Gantt(d.Machines)
        x = np.linspace(0, ga.Max_Itertions, ga.Max_Itertions)
        plt.plot(x, Best_fit, x, Worst_fit, x, Avg_fit,'-k')
        plt.title(
            'Best, Worst, Average Scheduling time Each iterator')
        plt.ylabel('Scheduling time')
        plt.xlabel('Number of iterations')
        plt.show()

    def Gantt(self,Machines):
        M = ['red', 'blue', 'yellow', 'orange', 'green', 'palegoldenrod', 'purple', 'pink', 'Thistle', 'Magenta',
             'SlateBlue', 'RoyalBlue', 'Cyan', 'Aqua', 'floralwhite', 'ghostwhite', 'goldenrod', 'mediumslateblue',
             'navajowhite',
             'navy', 'sandybrown', 'moccasin']
        for i in range(len(Machines)):
            Machine=Machines[i]
            Start_time=Machine.O_start
            End_time=Machine.O_end
            for i_1 in range(len(End_time)):
                # plt.barh(i,width=End_time[i_1]-Start_time[i_1],height=0.8,left=Start_time[i_1],\
                #          color=M[Machine.assigned_task[i_1][0]],edgecolor='black')
                # plt.text(x=Start_time[i_1]+0.1,y=i,s=Machine.assigned_task[i_1])
                plt.barh(i, width=End_time[i_1] - Start_time[i_1], height=0.8, left=Start_time[i_1], \
                         color='white', edgecolor='black')
                plt.text(x=Start_time[i_1] + (End_time[i_1] - Start_time[i_1])/2-0.5, y=i, s=Machine.assigned_task[i_1][0])
        plt.yticks(np.arange(i + 1), np.arange(1, i + 2))
        plt.title('Scheduling Gantt chart')
        plt.ylabel('Machines')
        plt.xlabel('Time')
        plt.show()

if __name__=='__main__':
    from test1 import Processing_time, Processing_Group, Machine_start_time, Time_efficent, Machine_buffer
    painter = JSPGAGraphPainter()
    painter.main(Processing_time, Processing_Group, Machine_start_time, Time_efficent, Machine_buffer)