from graphviz import Digraph

def create_complex_flowchart():
    dot = Digraph(comment='Complex Logic Flowchart')

    dot.node('A', 'Start', shape='ellipse')  # 椭圆形表示开始或结束节点

    dot.node('B', 'Readjust or Calibration', shape='rectangle')  # 矩形表示过程或操作步骤

    dot.node('B1', "Sensors' reading and sensors diff range normal? ", shape='diamond')  # 菱形表示判断或决策点

    dot.node('C', 'Input: All User Features available?', shape='parallelogram')  # 平行四边形表示输入/输出操作

    dot.node('D', 'Calibration to have user specific measurment data ', shape='rectangle')  # 菱形表示判断或决策点

    dot.node('F', 'Notidication to User:\nRe-calibrate Device or Re-adjust seat/monitor', shape='rectangle')

    dot.node('G', 'Start Timer', shape='rectangle')

    dot.node('G1', 'Input: Sensor 2, Sensor 4, \nFace Data, \nUser Weight, User Height, \nThreshold', shape='parallelogram')

    dot.node('G2', '400 (too close) < All Sensor < 850 (sensor miss-focus)? and Face Data Detected?', shape='diamond')

    # 计算差值和角度
    dot.node('H', 'Calculate Difference (Sensor 4 - Sensor 2)\nCalculate other input features', shape='rectangle')

    # 判断节点4: Sensor 4和Sensor 2的差值是否超过阈值
    dot.node('J', 'Model Outputs Abnormal Posture?', shape='diamond')
    dot.edge('J', 'L', label='Yes')
    dot.edge('J', 'L1', label='No')
    dot.node('L', 'Log: Abnormal Posture', shape='rectangle')
    dot.node('L1', 'Log: Normal Posture', shape='rectangle')
    dot.node('M', 'Check Logger Every X Minutes \n(X: user set alert frequency)', shape='rectangle')
    dot.node('N', 'Abnormal Counts > 80% of the time X?', shape='diamond')
    dot.node('O', 'Alert', shape='rectangle')
    dot.edge('O', 'O1')
    dot.node('O1', 'Alert Feedback enabled?', shape='diamond')
    dot.edge('O1', 'P', label='True')
    dot.edge('O1', 'R', label='False')
    dot.node('P', 'Alert Feedback True or False?', shape='diamond')
    dot.node('Q', 'Adjust Threshold', shape='rectangle')
    dot.node('R', 'Reset Timer', shape='rectangle')

    # 连线
    dot.edges(['AC', 'FB'])
    dot.edge('R', 'G')  # 让 R 指向 G1
    dot.edge('G1', 'G2')

    # dot.edge('D', 'E', label='Yes')
    dot.edge('C', 'G', label='Yes')
    dot.edge('C', 'D', label='No')
    dot.edge('D', 'G')
    # dot.edge('E', 'F', label='No')
    dot.edge('B1', 'G1', label='Yes')
    dot.edge('B1', 'F', label='No')
    dot.edge('B', 'B1')

    # 分开Start Detection和Input
    dot.edge('G', 'G1')


    # G2节点逻辑
    dot.edge('G2', 'H', label='Yes')  # 如果G2判断为是，进入H
    dot.edge('G2', 'F', label='No')  # 如果G2判断为否，进入F

    dot.edge('H', 'J')
    # dot.edge('I', 'J', label='No')
    # dot.edge('K', 'M')
    dot.edge('L', 'M')
    dot.edge('L1', 'M')

    dot.edge('M', 'N')
    dot.edge('N', 'O', label='Yes')
    dot.edge('N', 'R', label='No')  # 如果Logger Counts不超过80%，连接到Restart节点
    dot.edge('O', 'P')

    dot.edge('P', 'R', label='True')
    dot.edge('P', 'Q', label='False')

    dot.edge('Q', 'G1',label='New Threshold')
    dot.edge('Q', 'R')

    dot.render('complex_logic_flowchart_with_alert_feedback', format='png', cleanup=True)
    print("Flowchart saved as 'complex_logic_flowchart_with_alert_feedback.png'")

create_complex_flowchart()
