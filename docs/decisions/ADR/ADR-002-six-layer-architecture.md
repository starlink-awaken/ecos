# ADR-002: 采用六层架构模型

- **状态**: 已接受
- **日期**: 2026-05-13
- **决策者**: 夏同学 + Hermes

## 背景

需要一个结构化的架构模型来描述 eCOS 各组件的职责分层，避免关注点混淆。

## 决策

采用六层架构，从底到顶：

```
Layer 6: 反馈层    稳态监控，宪法执行器，偏差纠正
Layer 5: 行动层    工具调用，外部 API，Workflow 执行
Layer 4: 智能层    Agent委员会，推理引擎，规划器
Layer 3: 持久层    KOS + SharedBrain + 失败案例库
Layer 2: 感知层    Capture→Filter→Structure→Contextualize→Integrate
Layer 1: 宪法层    L0/L1/L2 不变量，GENOME.md
```

反馈层独立为第六层（而非嵌入其他层），因为稳态维护是贯穿全系统的横切关注点。

## 后果

- 正面：职责清晰，每层可独立演化
- 风险：层间通信标准化需要额外设计（SSB）
- 缓解：SSB Event Schema 作为 P0 任务尽快完成
