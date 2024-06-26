### 裁判系统串口协议（2024.1.22-V1.6.1）  
*多注意官方裁判系统串口协议更新*

1. 串口协议格式
> * frame_header 5-byte: SOF(0xA5) data_length seq CRC8
> * cmd_id 2-byte
> * data n-byte
> * frame_tail 2-byte
2. 雷达站所需命令码及声明
> * 0x0003 机器人血量数据，固定以 3Hz 频率发送
> * 0x0101 场地事件数据，固定以 1Hz 频率发送
> * 0x0102 补给站动作标识数据，补给站弹丸释放时触发发送
> * 0x020B 地面机器人位置数据，固定以 1Hz 频率发送(场地围挡在红方补给站附近的交点为坐标原点，沿场地长边向蓝方为 X 轴正方向，沿场地短边向红方停机坪为 Y 轴正方向。)
> * 0x020C 雷达标记进度数据，固定以 1Hz 频率发送
> * 0x020E 雷达自主决策信息同步，固定以 1Hz 频率发送
> * 0x0301 机器人交互数据，发送方触发发送，频率上限为 10Hz(雷达站自主决策)
> * 0x0305 选手端小地图接收雷达数据，频率上限为 10Hz
> * 0x0308 选手端小地图接收机器人数据，频率上限为 3Hz
3. 小地图交互数据
> * 雷达可通过常规链路向己方所有选手端发送对方机器人的坐标数据，该位置会在己方选手端小地图显示。
> * 己方机器人可通过常规链路向己方任意选手端发送自定义的消息，该消息会在己方选手端特定位置显示。
4. 图传链路数据说明
5. 非链路数据说明
6. ID编号说明