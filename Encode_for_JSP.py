import numpy as np
import random
 
class Encode:
    def __init__(self,Matrix,Pop_size,J,J_num,M_num, Processing_group, Processing_weight):
        self.Matrix=Matrix      #工件各工序对应各机器加工时间矩阵
        self.GS_num=int(0.6*Pop_size)      #全局选择初始化
        self.LS_num=int(0.3*Pop_size)     #局部选择初始化
        self.RS_num=int(0.1*Pop_size)     #随机选择初始化
        self.J=J                #各工件对应的工序数
        self.J_num=J_num        #工件数
        self.M_num=M_num        #机器数
        self.Processing_group = Processing_group #工件分组
        self.Processing_weight = Processing_weight
        self.CHS=[]
        self.Len_Chromo=0
        for i in J.values():
            self.Len_Chromo+=i
 
    # 生成工序准备的部分
    def OS_ListNew(self):
        tmp = []
        for i in range(len(self.J)):
            tmp.append(i)
        if (self.Processing_group is not None and len(self.Processing_group) > 0):
            #工件组合（加工顺序必须固定）
            tmp_group = []
            for group in self.Processing_group:
                if (len(group) > 0):
                    tmp_group.append(group)
                    for i in group:
                        tmp.remove(i)
            for i in tmp:
                tmp_group.append([i])
            random.shuffle(tmp_group)
            tmp.clear()
            for group in tmp_group:
                for i in group:
                    tmp.append(i)
        else:
            random.shuffle(tmp)
        OS_list=[]
        for i in tmp:
            O_num = self.J[i + 1]
            for o in range(O_num):
                OS_list.append(i)
        return OS_list
    #生成工序准备的部分
    def OS_List(self):
        OS_list=[]
        for k,v in self.J.items():
            OS_add=[k-1 for j in range(v)]
            OS_list.extend(OS_add)
        return OS_list
 
    #生成初始化矩阵
    def CHS_Matrix(self, C_num):  # C_num:所需列数
        return np.zeros([C_num, self.Len_Chromo], dtype=int)
 
    def Site(self,Job,Operation):
        O_num = 0
        for i in range(len(self.J)):
            if i == Job:
                return O_num + Operation
            else:
                O_num = O_num + self.J[i + 1]
        return O_num
 
    #全局选择初始化
    def Global_initial(self):
        MS=self.CHS_Matrix(self.GS_num)
        OS_list= self.OS_ListNew() # 生成工序排序部分
        OS=self.CHS_Matrix(self.GS_num)
        WS=np.zeros([self.GS_num, self.J_num], dtype=int)
        WS_list = self.WS_List()
        for i in range(self.GS_num):
            Machine_time = np.zeros(self.M_num, dtype=float)  # 机器时间初始化
            OS[i] = np.array(OS_list)
            WS[i] = np.array(WS_list)
            GJ_list = [i_1 for i_1 in range(self.J_num)]
            random.shuffle(GJ_list)
            for g in GJ_list:  # 随机选择工件集的第一个工件,从工件集中剔除这个工件
                h = self.Matrix[g]  # 第一个工件含有的工序
                for j in range(len(h)):  # 从工件的第一个工序开始选择机器
                    D = h[j]
                    List_Machine_weizhi = []
                    for k in range(len(D)):  # 每道工序可使用的机器以及机器的加工时间
                        Useing_Machine = D[k]
                        if Useing_Machine is not None and len(Useing_Machine) > 0:  # 确定可加工该工序的机器
                            List_Machine_weizhi.append(k)
                    Machine_Select = []
                    for Machine_add in List_Machine_weizhi:  # 将这道工序的可用机器时间和以前积累的机器时间相加
                        #  比较可用机器的时间加上以前累计的机器时间的时间值，并选出时间最小
                        Machine_Select.append(Machine_time[Machine_add] + min(D[Machine_add]))
                    Min_time = min(Machine_Select)
                    K = Machine_Select.index(Min_time)
                    I = List_Machine_weizhi[K]
                    Machine_time[I] = Min_time
                    site=self.Site(g,j)
                    MS[i][site] = K
        CHS1 = np.hstack((MS, OS, WS))
        return CHS1
 
 
    #局部选择初始化
    def Local_initial(self):
        MS = self.CHS_Matrix(self.LS_num)
        OS_list = self.OS_ListNew()# 生成工序排序部分
        OS = self.CHS_Matrix(self.LS_num)
        WS=np.zeros([self.LS_num, self.J_num], dtype=int)
        WS_list = self.WS_List()
        for i in range(self.LS_num):
            (OS_list)  
            OS_gongxu = OS_list
            OS[i] = np.array(OS_gongxu)
            WS[i] = np.array(WS_list)
            GJ_list = [i_1 for i_1 in range(self.J_num)]
            for g in GJ_list:
                Machine_time = np.zeros(self.M_num)  # 机器时间初始化
                h =self.Matrix[g]   # 第一个工件及其对应工序的加工时间
                for j in range(len(h)):  # 从工件的第一个工序开始选择机器
                    D = h[j]
                    List_Machine_weizhi = []
                    for k in range(len(D)):  # 每道工序可使用的机器以及机器的加工时间
                        Useing_Machine = D[k]
                        if Useing_Machine is None or len(Useing_Machine) == 0:  # 确定可加工该工序的机器
                            continue
                        else:
                            List_Machine_weizhi.append(k)
                    Machine_Select = []
                    for Machine_add in List_Machine_weizhi:  # 将这道工序的可用机器时间和以前积累的机器时间相加
                        Machine_time[Machine_add] = Machine_time[Machine_add] + min(D[Machine_add])  # 比较可用机器的时间加上以前累计的机器时间的时间值，并选出时间最小
                        Machine_Select.append(Machine_time[Machine_add])
                    Machine_Index_add = Machine_Select.index(min(Machine_Select))
                    site = self.Site(g, j)
                    MS[i][site] = MS[i][site] + Machine_Index_add
        CHS1 = np.hstack((MS, OS, WS))
        return CHS1
 
    def Random_initial(self):
        MS = self.CHS_Matrix(self.RS_num)
        OS_list = self.OS_ListNew()# 生成工序排序部分
        OS = self.CHS_Matrix(self.RS_num)
        WS=np.zeros([self.RS_num, self.J_num], dtype=int)
        WS_list = self.WS_List_random() #生产标定砝码部分
        for i in range(self.RS_num):
            OS_gongxu = OS_list
            WS[i] = np.array(WS_list)
            OS[i] = np.array(OS_gongxu)
            GJ_list = [i_1 for i_1 in range(self.J_num)]
            A = 0
            for gon in GJ_list:
                Machine_time = np.zeros(self.M_num)  # 机器时间初始化
                g = gon  # 随机选择工件集的第一个工件   #从工件集中剔除这个工件
                h = self.Matrix[g]  # 第一个工件及其对应工序的加工时间
                for j in range(len(h)):  # 从工件的第一个工序开始选择机器
                    D = h[j]
                    List_Machine_weizhi = []
                    Site=0
                    for k in range(len(D)):  # 每道工序可使用的机器以及机器的加工时间
                        if D[k] is None or len(D[k]) == 0:  # 确定可加工该工序的机器
                            continue
                        else:
                            List_Machine_weizhi.append(Site)
                            Site+=1
                    Machine_Index_add = random.choice(List_Machine_weizhi)
                    MS[i][A] = MS[i][A] + Machine_Index_add
                    A += 1
        CHS1 = np.hstack((MS, OS, WS))
        return CHS1
    #平均分配标定使用的砝码
    def WS_List(self):
        WS_list=[]
        ProcessingWeight = self.Processing_weight
        for i in range(len(ProcessingWeight)):
            WS_list.append(random.randint(0, len(ProcessingWeight[i]) - 1))
        return WS_list
    # 随机选择标定使用的砝码
    def WS_List_random(self):
        WS_list=[]
        ProcessingWeight = self.Processing_weight
        for i in range(len(ProcessingWeight)):
            WS_list.append(random.randint(0, len(ProcessingWeight[i]) - 1))
        return WS_list