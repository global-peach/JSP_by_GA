from model import HFSPGAInput
from Jobs import Job
from Machines import Machine_Time_window
import numpy as np
 
class Decode:
    def __init__(self, J, GAInput: HFSPGAInput, M_num):
        self.Processing_time = GAInput.ProcessingTime
        self.Machine_start_time = GAInput.MachineStartTime
        self.Time_efficent = GAInput.TimeEfficent
        self.Machine_buffer = GAInput.MachineBuffer
        self.GAInput = GAInput
        self.Scheduled = []  # 已经排产过的工序
        self.M_num = M_num
        self.Machines: list[Machine_Time_window] = []  # 存储机器类
        self.fitness = 0
        self.IsWorst = GAInput.IsWorst
        self.J=J            #
        for j in range(M_num):
            self.Machines.append(Machine_Time_window(j))
        self.Machine_State = np.zeros(M_num, dtype=int)  # 在机器上加工的工件是哪个
        self.Jobs: list[Job] = []     #存储工件类
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
    def Earliest_Start(self,Job: int,O_num,Machine: int,JM,Weight:int): # 计算工序的开始时间
        last_O_end = self.Jobs[Job].Last_Processing_end_time  # 上道工序结束时间
        Selected_Machine=Machine
        #计算真正的机器（C1~C4必须在相同工位进行，包装工序要在对应的标定工位之后进行）
        index = self.Jobs[Job].Current_Processed()
        if index == 2 or index == 4: #装配2、接线
            Selected_Machine = self.Jobs[Job].J_machine[0] #在装配1工位进行
        elif index == 6: #包装工序
            Selected_Machine = self.Jobs[Job].Last_Processing_Machine + 2 #所在标定工位+2即为包装工位
        machine_start = 0   # 机器开工时间
        if (self.Machine_start_time is not None and len(self.Machine_start_time) > Selected_Machine):
            machine_start = self.Machine_start_time[Selected_Machine]
        # M_window = self.Machines[Selected_Machine].Empty_time_window()
        # M_Tstart = M_window[0]
        # M_Tend = M_window[1]
        # M_Tlen = M_window[2]
        Machine_end_time = max(self.Machines[Selected_Machine].End_time, machine_start)         #上一道工序的结束时间
        Next_Machine_start_time = self.Get_Job_Shift_Time(self.Machines[Selected_Machine],JM)   #上一道工序的流转时刻
        ealiest_start = max(last_O_end, Machine_end_time, Next_Machine_start_time)
        #生产资源需求：
        #C1~C4工位多工人少，进入工位后，需要判断是否有空余的工人进行加工，如没有，则需要等待
        resource_start_time = 0
        if Selected_Machine < 4:
            resource_start_time = self.Get_C_Time(ealiest_start)
        #标定1、2工位需要使用砝码，若标定工位现有砝码不同，则需要等待换型完成；若砝码已在其它标定工位使用，则需要等其结束再换型
        elif Selected_Machine == 6 or Selected_Machine == 7:
            WeightName = self.GAInput.ProcessingWeight[Job][Weight]
            resource_start_time = self.Get_Weight_Time(ealiest_start, Selected_Machine, WeightName)
        ealiest_start = max(ealiest_start, resource_start_time)
        # if M_Tlen is not None:  # 此处为全插入时窗
        #     for le_i in range(len(M_Tlen)):
        #         if M_Tlen[le_i] >= P_t:
        #             if M_Tstart[le_i] >= last_O_end:
        #                 ealiest_start=M_Tstart[le_i]
        #                 break
        #             if M_Tstart[le_i] < last_O_end and M_Tend[le_i] - last_O_end >= P_t:
        #                 ealiest_start = last_O_end
        #                 break
        M_Ealiest = ealiest_start # 加工开始时间
        End_work_time = M_Ealiest # 计算跳过休息时间的加工结束时间
        rest_work = 1 # 剩余加工进度，初始100%
        P_t = 0 # 总加工时间
        # P_t=self.Processing_time[Job][O_num][Machine]
        for i in range(len(self.Time_efficent)):
            start = self.Time_efficent[i] # 开始时间
            end = 9999 # 结束时间
            if i + 1 < len(self.Time_efficent):
                end = self.Time_efficent[i + 1]
            efficent = self.Processing_time[Job][O_num][Machine][i] # 根据能效获取节拍
            if end < M_Ealiest:
                continue
            if start <= M_Ealiest and end > M_Ealiest:
                # 找到了开工时间
                if efficent == -1:
                    # 最早开工时间落在了休息时间，往后顺延
                    M_Ealiest = end
                    End_work_time = end
                    continue
            if End_work_time < end:
                if efficent == -1:
                    # 休息时间，结束时间累加
                    End_work_time = end
                else:
                    # 计算结束时间
                    if end - End_work_time >= efficent * rest_work:
                        # 时间段内能做完
                        End_work_time += efficent * rest_work
                        P_t += efficent * rest_work
                        break
                    else:
                        # 不能做完，计算完成度
                        rest_work -= (end - End_work_time) / efficent
                        P_t += end - End_work_time
                        End_work_time = end
        return M_Ealiest, Selected_Machine, P_t, O_num,last_O_end,End_work_time
    #解码
    def Decode_1(self,CHS,Len_Chromo):
        MS=list(CHS[0:Len_Chromo])
        OS=list(CHS[Len_Chromo:2*Len_Chromo])
        WS=list(CHS[2*Len_Chromo:2*Len_Chromo+len(self.Jobs)])
        Needed_Matrix=self.Order_Matrix(MS)
        JM=Needed_Matrix[0]
        for i in OS:
            Job=i
            O_num=self.Jobs[Job].Current_Processed()
            Machine: int=JM[Job][O_num]
            weight = WS[i]
            Para=self.Earliest_Start(Job, O_num, Machine, JM, weight)
            self.Jobs[Job]._Input(Para[0],Para[5],Para[1])
            if Para[5]>self.fitness:
                self.fitness=Para[5]
            self.Machines[Para[1]]._Input(Job, Para[0], Para[5], Para[2], Para[3], weight)
        return self.fitness if self.IsWorst is False else 1 / self.fitness
 
    
    def Get_Job_Shift_Time(self, machine: Machine_Time_window,JM: list[list[int]]):
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
                        if len(next_o_machine.assigned_task) > 0 and next_o_machine.assigned_task.__contains__([last_task[0], last_task[1] + 1]):
                            next_machine_time = next_o_machine.O_start[next_o_machine.assigned_task.index([last_task[0], last_task[1] + 1])]
                        return max(machine.End_time, next_machine_time)
                    else:
                        #下一个机器有buffer
                        return machine.End_time
            else:
                #工件所有工序加工完成，返回加工完成时间
                return machine.End_time
    #获取C1~C4的首个工人可用时间    
    def Get_C_Time(self, startTime):
        CWorkerCount = self.GAInput.ResourceConfig["CWorkerCount"]
        # 先计算在startTime时刻，C1~C4有多少个正在加工的工件
        CJobCount = 0
        endTime = []
        for i in range(4):
            machine = self.Machines[i]
            if machine.End_time > startTime:
                CJobCount += 1
                endTime.append(machine.End_time)
        #若可用工人数量小于1，则等待时间为第一个工件结束的时间
        if CJobCount < CWorkerCount:
            return startTime
        else:
            return min(endTime)

    #获取标定可用时间
    def Get_Weight_Time(self, startTime: int, machine: int, weightName: str):
        resourceTime = startTime
        Weight1TCount = self.GAInput.ResourceConfig["1T"]
        Weight2TCount = self.GAInput.ResourceConfig["2T"]
        Weight3TCount = self.GAInput.ResourceConfig["3T"]
        #标定1
        machine1 = self.Machines[6]
        machine1End = 0
        machine1Weight1TUsingCount = 0
        machine1Weight2TUsingCount = 0
        machine1Weight3TUsingCount = 0
        if  len(machine1.assigned_task) > 0:
            lastWeightIndex = machine1.worker_for_task[-1]
            lastJobIndex = machine1.assigned_task[-1][0] - 1
            last = self.GAInput.ProcessingWeight[lastJobIndex][lastWeightIndex]
            if last == '1T':
                machine1Weight1TUsingCount += 1
            elif last ==  '2T':
                machine1Weight2TUsingCount += 1
            elif last ==  '3T':
                machine1Weight3TUsingCount += 1
            elif last ==  '6T':
                machine1Weight3TUsingCount += 2  
        if machine1.End_time > startTime:
                machine1End = machine1.End_time
        #标定2
        machine2 = self.Machines[7]
        machine2End = 0
        machine2Weight1TUsingCount = 0
        machine2Weight2TUsingCount = 0
        machine2Weight3TUsingCount = 0
        if  len(machine2.assigned_task) > 0:
            lastWeightIndex = machine2.worker_for_task[-1]
            lastJobIndex = machine2.assigned_task[-1][0] - 1
            last = self.GAInput.ProcessingWeight[lastJobIndex][lastWeightIndex]
            if last == '1T':
                machine2Weight1TUsingCount += 1
            elif last == '2T':
                machine2Weight2TUsingCount += 1
            elif last == '3T':
                machine2Weight3TUsingCount += 1
            elif last == '6T':
                machine2Weight3TUsingCount += 2  
            if machine2.End_time > startTime:
                machine2End = machine2.End_time
        if machine == 6:
            if machine1End > resourceTime:
                resourceTime = machine1End
            #1.判断需用砝码是否有剩余，如果没有，需要等待使用结束
            #2.判断所在标定工位上一个标定的是否是相同，如果不是，需要增加换型时间
            if weightName == '1T':
                if machine2Weight1TUsingCount + 1 > Weight1TCount and machine2End > machine1End:
                    resourceTime = machine2End
                if machine1Weight1TUsingCount == 0:
                    resourceTime += 5
            elif weightName ==  '2T':
                if machine2Weight2TUsingCount + 1 > Weight2TCount and machine2End > machine1End:
                    resourceTime = machine2End
                if machine1Weight2TUsingCount == 0:
                    resourceTime += 5
            elif weightName ==  '3T':
                if machine2Weight3TUsingCount + 1 > Weight3TCount and machine2End > machine1End:
                    resourceTime = machine2End
                if machine1Weight3TUsingCount == 0:
                    resourceTime += 5
            elif weightName ==  '6T':
                if machine2Weight3TUsingCount + 2 > Weight3TCount and machine2End > machine1End:
                    resourceTime = machine2End
                if machine1Weight3TUsingCount < 2:
                    resourceTime += 5
        elif machine == 7:
            if machine2End > resourceTime:
                resourceTime = machine2End
            #1.判断需用砝码是否有剩余，如果没有，需要等待使用结束
            #2.判断所在标定工位上一个标定的是否是相同，如果不是，需要增加换型时间
            if weightName == '1T':
                if machine1Weight1TUsingCount + 1 > Weight1TCount and machine1End > machine2End:
                    resourceTime = machine2End
                if machine2Weight1TUsingCount == 0:
                    resourceTime += 5
            elif weightName ==  '2T':
                if machine1Weight2TUsingCount + 1 > Weight2TCount and machine1End > machine2End:
                    resourceTime = machine2End
                if machine2Weight2TUsingCount == 0:
                    resourceTime += 5
            elif weightName ==  '3T':
                if machine1Weight3TUsingCount + 1 > Weight3TCount and machine1End > machine2End:
                    resourceTime = machine2End
                if machine2Weight3TUsingCount == 0:
                    resourceTime += 5
            elif weightName ==  '6T':
                if machine1Weight3TUsingCount + 2 > Weight3TCount and machine1End > machine2End:
                    resourceTime = machine2End
                if machine2Weight3TUsingCount < 2:
                    resourceTime += 5
        return resourceTime