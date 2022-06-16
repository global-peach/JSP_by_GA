# JSP_by_GA
GA（遗传算法）求解JSP（车间调度问题）

本项目参考了CSDN专栏[Python实现车间调度或论文](https://blog.csdn.net/crazy_girl_me/category_11066480.html)中FJSP（柔性车间调度问题）的Python实现

并在其基础上实现了如下特殊需求：
1. 工件在机器间流转：本机器上加工的工件要流转到下一个机器，本机器才能开始加工下一个工件。（与原作的时间窗计算方式不同）
2. 工件组合：一组工件的加工顺序必须固定
3. 机器开工时间：由于部分机器需要完成上一批次加工的工件，排产时需要考虑机器参与本次排产的开工时间

两种使用方法：
1. 运行FJSPGA.py文件，其中的main函数可加载test1-3中的测试用例，并使用GA进行求解，最终输出最优解的甘特图，以及迭代过程中种群最大、最小、平均适应度曲线。
2. 运行JSPGAHttpServer.py文件，将提供HTTP服务，并使用GA进行求解，最终返回各机器上各工件的加工起始、结束时间。
