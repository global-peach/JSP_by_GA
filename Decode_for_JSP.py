from Jobs import Job
from Machines import Machine_Time_window
import numpy as np
 
class Decode:
    def __init__(self,J,Processing_time,M_num, Machine_start_time, Time_efficent, Machine_buffer):
        self.Processing_time = Processing_time
        self.Machine_start_time = Machine_start_time
        self.Time_efficent = Time_efficent
        self.Machine_buffer = Machine_buffer
        self.Scheduled = []  # 已经排产过的工序
        self.M_num = M_num
        self.Machines = []  # 存储机器类
        self.fitness = 0
        self.J=J            #
        for j in range(M_num):
            self.Machines.append(Machine_Time_window(j))
        self.Machine_State = np.zeros(M_num, dtype=int)  # 在机器上加工的工件是哪个
        self.Jobs = []     #存储工件类
        for k, v in J.items():
            self.Jobs.append(Job(k, v))
    #时间顺序矩阵和机器顺序矩阵
    def Order_Matrix(self,MS):
        JM=[]
        T=[]
        Ms_decompose=[]
        Site=0
        for S_i in self.J.values():
            Ms_decompose.append(MS[Site:Site+S_i])
            Site+=S_i
        for i in range(len(Ms_decompose)):
            JM_i=[]
            T_i=[]
            for j in range(len(Ms_decompose[i])):
                O_j=self.Processing_time[i][j]
                M_ij=[]
                T_ij=[]
                for Mac_num in range(len(O_j)):  # 寻找MS对应部分的机器时间和机器顺序
                    if O_j[Mac_num] is not None and len(O_j[Mac_num]) > 0:
                        M_ij.append(Mac_num)
                        T_ij.append(O_j[Mac_num])
                    else:
                        continue
                JM_i.append(M_ij[Ms_decompose[i][j]])
                T_i.append(T_ij[Ms_decompose[i][j]])
            JM.append(JM_i)
            T.append(T_i)
        return JM,T
    def Earliest_Start(self,Job,O_num,Machine,JM): # 计算工序的开始时间
        last_O_end = self.Jobs[Job].Last_Processing_end_time  # 上道工序结束时间
        Selected_Machine=Machine
        machine_start = 0   # 机器开工时间
        if (self.Machine_start_time is not None and len(self.Machine_start_time) > Selected_Machine):
            machine_start = self.Machine_start_time[Selected_Machine]
        M_window = self.Machines[Selected_Machine].Empty_time_window()
        M_Tstart = M_window[0]
        M_Tend = M_window[1]
        M_Tlen = M_window[2]
        Machine_end_time = max(self.Machines[Selected_Machine].End_time, machine_start)
        #流转需求:本机器上加工的工件要流转到下一个机器，本机器才能开始加工下一个工件， 与原作的时间窗不同
        Next_Machine_start_time = self.Get_Job_Shift_Time(self.Machines[Selected_Machine],JM)
        ealiest_start = max(last_O_end, Machine_end_time, Next_Machine_start_time)
        # if M_Tlen is not None:  # 此处为全插入时窗
        #     for le_i in range(len(M_Tlen)):
        #         if M_Tlen[le_i] >= P_t:
        #             if M_Tstart[le_i] >= last_O_end:
        #                 ealiest_start=M_Tstart[le_i]
        #                 break
        #             if M_Tstart[le_i] < last_O_end and M_Tend[le_i] - last_O_end >= P_t:
        #                 ealiest_start = last_O_end
        #                 break
        M_Ealiest = ealiest_start
        # P_t=self.Processing_time[Job][O_num][Machine]
        efficent = -1 # 根据开始时间获取能效
        for e in self.Time_efficent:
            if M_Ealiest >= e:
                efficent += 1
            else:
                if self.Processing_time[Job][O_num][Machine][efficent] == -1: # 该时间段休息，不开工
                    efficent += 1
                    if efficent < len(self.Time_efficent):
                        M_Ealiest = self.Time_efficent[efficent]
                    else:
                        raise Exception('检测到无法完成排产')
                else:
                    break
        #efficent = min(efficent, len(self.Processing_time[Job][O_num][Machine]) - 1)
        P_t = self.Processing_time[Job][O_num][Machine][efficent] # 根据能效获取节拍
        End_work_time = M_Ealiest + P_t
        return M_Ealiest, Selected_Machine, P_t, O_num,last_O_end,End_work_time
    def Get_Job_Shift_Time(self, machine,JM):
        #也就是本机器上一个工件的下一道工序所在机器的开始时间(流转时刻)
        #获取本机器上一个工件
        if len(machine.assigned_task) == 0:
            #机器未加工过任何工件
            return 0
        else:
            last_task = machine.assigned_task[-1]
            last_job = self.Jobs[last_task[0] - 1]
            last_o = last_task[1]
            if last_job.Operation_num > last_o:
                #还有未完成的工序
                next_o_machine = self.Machines[JM[last_task[0] - 1][last_task[1]]]
                #判断下一个机器是否有buffer
                if self.Machine_buffer is not None:
                    index = -1
                    for i in self.Machine_buffer:
                        if i ==  next_o_machine.Machine_index:
                            index = i
                            break
                    if index == -1:
                        #由于下一个机器也会有加工的工件，而其流转时刻又受下下个机器影响，所以需要计算
                        next_machine_time = 0
                        if len(next_o_machine.assigned_task) > 0:
                            next_machine_time = next_o_machine.O_start[next_o_machine.assigned_task.index([last_task[0], last_task[1] + 1])]
                        return max(machine.End_time, next_machine_time)
                    else:
                        #下一个机器有buffer
                        return machine.End_time
            else:
                #工件所有工序加工完成，返回加工完成时间
                return machine.End_time
    #解码
    def Decode_1(self,CHS,Len_Chromo):
        MS=list(CHS[0:Len_Chromo])
        OS=list(CHS[Len_Chromo:2*Len_Chromo])
        Needed_Matrix=self.Order_Matrix(MS)
        JM=Needed_Matrix[0]
        for i in OS:
            Job=i
            O_num=self.Jobs[Job].Current_Processed()
            Machine=JM[Job][O_num]
            Para=self.Earliest_Start(Job,O_num,Machine,JM)
            self.Jobs[Job]._Input(Para[0],Para[5],Para[1])
            if Para[5]>self.fitness:
                self.fitness=Para[5]
            self.Machines[Machine]._Input(Job,Para[0],Para[2],Para[3])
        return self.fitness
 
    