from graphviz import Digraph
# Dear TEAM, I have created a flowchart for the logic of device monitoring.
# Please consider when building the GUI. Thank you!
def create_complex_flowchart():
    dot = Digraph(comment='Complex Logic Flowchart')

    # 开始节点
    dot.node('A', 'Start', shape='ellipse')  # 椭圆形表示开始或结束节点

    # 要求保持治理坐姿
    dot.node('B', 'Calibration', shape='rectangle')  # 矩形表示过程或操作步骤
    # 判断节点1: 判断Sensor是否都在400-1200范围内
    dot.node('B1', "Sensors' reading and sensors diff range normal? ", shape='diamond')  # 菱形表示判断或决策点
    # 输入节点
    dot.node('C', 'Input: User Features available?', shape='parallelogram')  # 平行四边形表示输入/输出操作

    # 判断节点1: 判断Sensor是否都在400-1200范围内
    # dot.node('D', '400 (too close) < All Sensor < 850 (sensor miss-focus)? ', shape='diamond')  # 菱形表示判断或决策点

    # # 判断节点2: 判断人脸数据是否有识别到
    # dot.node('E', 'Face Data Detected?', shape='diamond')

    # 重新矫正设备
    dot.node('F', 'Notidication to User:\nRe-calibrate Device or Re-adjust seat/monitor', shape='rectangle')

    # 开始检测节点
    dot.node('G', 'Start Timer', shape='rectangle')

    # 输入节点（开始检测后的输入）
    dot.node('G1', 'Input: Sensor 2, Sensor 4, \nFace Data, \nUser Weight, User Height, \nThreshold', shape='parallelogram')

    dot.node('G2', '400 (too close) < All Sensor < 850 (sensor miss-focus)? and Face Data Detected?', shape='diamond')

    # 计算差值和角度
    dot.node('H', 'Calculate Difference (Sensor 4 - Sensor 2)\nCalculate other input features\nMake Predictions', shape='rectangle')

    # # 判断节点3: 头部倾斜角度是否大于20度
    # dot.node('I', 'Head Tilt > 20°?', shape='diamond')

    # 判断节点4: Sensor 4和Sensor 2的差值是否超过阈值
    dot.node('J', 'Model One Outputs 0?', shape='diamond')
    dot.node('J1', 'Model2and3 Output 0?', shape='diamond')
    dot.edge('J', 'J1', label='No')
    dot.edge('J1', 'L', label='Yes')
    dot.edge('J1', 'L1', label='No')
    # 输出到logger
    # dot.node('K', 'Log: Head Tilt Abnormal', shape='rectangle')
    dot.node('L', 'Log: Forward Head Abnormal', shape='rectangle')
    dot.node('L1', 'Log: Forward Head Normal', shape='rectangle')

    # Timer节点
    #dot.node('T', 'Start Timer', shape='rectangle')

    # 每5分钟检查一次logger
    dot.node('M', 'Check Logger Every X Minutes \n(X: user set alert frequency)', shape='rectangle')

    # 判断logger的数量是否大于80%
    dot.node('N', 'Abnormal Counts > 80% of the time X?', shape='diamond')

    # 发出警报
    dot.node('O', 'Alert', shape='rectangle')

    # 警报反馈节点
    dot.node('P', 'Alert Feedback True or False?', shape='diamond')

    # 调整阈值
    dot.node('Q', 'Adjust Threshold', shape='rectangle')

    # 增加的Restart节点
    dot.node('R', 'Reset Timer', shape='rectangle')

    # 连线
    dot.edges(['AC', 'FB'])
    dot.edge('R', 'G')  # 让 R 指向 G1
    dot.edge('G1', 'G2')

    # dot.edge('D', 'E', label='Yes')
    dot.edge('C', 'G', label='Yes')
    # dot.edge('E', 'G', label='Yes')
    # dot.edge('E', 'F', label='No')
    dot.edge('B1', 'G1', label='Yes')
    dot.edge('B1', 'F', label='No')
    dot.edge('B', 'B1')

    # 分开Start Detection和Input
    dot.edge('G', 'G1')
    #dot.edge('G1', 'H')
    #dot.edge('T', 'H')
    #dot.edge('G1', 'T', constraint='false')

    # G2节点逻辑
    dot.edge('G2', 'H', label='Yes')  # 如果G2判断为是，进入H
    dot.edge('G2', 'F', label='No')  # 如果G2判断为否，进入F

    dot.edge('H', 'J')
    # dot.edge('I', 'J', label='No')
    # dot.edge('I', 'K', label='Yes')
    dot.edge('J', 'L', label='Yes')
    # dot.edge('J', 'L1', label='Normal')  # 这里改为连接Restart节点
    # dot.edge('K', 'M')
    dot.edge('L', 'M')
    dot.edge('L1', 'M')

    # 新增的逻辑部分
    dot.edge('M', 'N')
    dot.edge('N', 'O', label='Yes')
    dot.edge('N', 'R', label='No')  # 如果Logger Counts不超过80%，连接到Restart节点
    dot.edge('O', 'P')

    # 警报反馈处理
    dot.edge('P', 'R', label='True')
    dot.edge('P', 'Q', label='False')

    # 调整阈值后的逻辑
    dot.edge('Q', 'G1',label='New Threshold')
    dot.edge('Q', 'R')

    # 渲染并保存图像
    dot.render('complex_logic_flowchart_with_alert_feedback', format='png', cleanup=True)
    print("Flowchart saved as 'complex_logic_flowchart_with_alert_feedback.png'")

# 创建复杂流程图
create_complex_flowchart()
