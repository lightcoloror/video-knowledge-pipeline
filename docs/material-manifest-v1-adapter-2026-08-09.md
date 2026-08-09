# VKP `material-manifest.v1` 生产薄适配

更新时间：2026-08-09 11:25:00 +08:00
执行者：Codex（GPT-5.6 Sol）
状态：local_verified

## 结论

VKP 可以把现有 Bundle 的规范逐字稿、关键帧、Timeline 时间证据和 Bundle 元数据投影为共享 `material-manifest.v1`。产物是只读、内容寻址的引用信封，不复制逐字稿正文，不推断网页文档节点顺序，也不授予 Provider 调用、上传、审核或发布权限。

稳定入口：

```powershell
python -m video_knowledge_pipeline.cli material-manifest <bundle>
python -m video_knowledge_pipeline.cli material-manifest-validate <bundle>
```

默认产物：`<bundle>/exports/material-manifest.v1.json`。

## 复用关系

- 共享合同：工作区 `docs/local-tools/contracts/linkage-contract-catalog.v1.json`。
- VKP 原生来源：`manifest.json`、`timeline.json`、Smart Summary 已有 canonical transcript selector、artifact evidence、dependency snapshot 和原子 JSON 写入。
- WCF 继续拥有 `weixin-native-document.v1` 的图文混排 source order、资源完整性和 gallery 禁止语义。VKP 只声明 `video_temporal_only`，不会伪造文档节点顺序。
- ebook manifest、模型网关、consent、approval、review 和 run registry 均未复制或修改。

## 输出合同

- `schema=material-manifest.v1`
- `schema_version=1.0`
- `native_contract=video_knowledge_pipeline.material_reference.v1`
- `bundle`：Bundle manifest 和 Timeline 的 Bundle 内相对路径、字节数、SHA-256 与 MIME。
- `transcript`：规范逐字稿引用；`content_embedded=false`。
- `timeline_items`：严格递增的 `source_order`、Timeline index、毫秒时间范围、evidence IDs 和关键帧引用。
- `dependency_snapshot`：绑定 manifest、Timeline、逐字稿和每个唯一关键帧。
- `authority_boundary`：固定禁止执行、外发、consent、review approval、Timeline 修改和文档顺序声明。
- `manifest_sha256`：绑定除自身 ID/hash 外的完整清单身份。

## Fail-closed 条件

- Schema 或版本不匹配。
- manifest identity/hash 漂移。
- canonical transcript 缺失或位于 Bundle 外。
- 关键帧缺失、位于 Bundle 外或精确时间戳越过 Timeline 范围。
- Timeline 不是数组、项目损坏、index 重复、时间倒序或 source order 不连续。
- manifest、Timeline、逐字稿或关键帧在清单生成后发生变化。
- 输出路径越过 Bundle。

## 变更理由

| change_id | 意图 | 决策 | 理由 | 证据 | 生效范围 | 回滚 |
|---|---|---|---|---|---|---|
| VKP-MATERIAL-001 | 让 VKP 成为共享材料清单的真实 producer | 在既有 `creative_contract_bridge` 增加只读引用投影 | 该模块已经负责跨项目候选合同和权限边界 | 共享 catalog 固定其 SHA/commit；原关联基线 12/12 | Bundle 派生 JSON；不改 Timeline/原生 manifest | 删除 material 构建/校验函数与 CLI |
| VKP-MATERIAL-002 | 统一版本、字段和权限常量 | 随包发布 Draft 2020-12 JSON Schema | clone/安装后不能依赖工作区外部 Schema 才能校验 | jsonschema 已是 VKP 核心依赖 | `material-manifest.v1` 输出 | 删除 Schema 并移除 package-data 行 |
| VKP-MATERIAL-003 | 防止旧清单继续消费变化后的 Bundle | 复用 artifact dependency snapshot，并排除非确定性创建时间 | VKP 已有成熟 freshness/hash 实现；重复运行应字节一致 | stale fixture 和 double-run 回归 | manifest/Timeline/transcript/keyframe lineage | 删除 snapshot 字段；原 Bundle 不受影响 |
| VKP-MATERIAL-004 | 防止 metadata 被误当授权 | 固定所有 authority 字段为 false，并拒绝额外字段 | 共享 manifest 只负责链接，不拥有 consent/review/provider 权限 | JSON Schema const 与负例测试 | Local Tools、BookWiki、Content Studio、research-content-production 消费端 | 停止发出 facade；消费者继续读取 VKP 原生 Bundle |

## 验证

- 正例：规范转写、两段时间证据和两张关键帧可生成并验证。
- 负例：版本、hash、缺帧、越界、陈旧 Bundle、错误 source order、损坏输入全部 fail-closed。
- 幂等：相同 Bundle 连续生成两次，返回对象和落盘字节均一致。
- 关联回归：creative bridge、model output contract 和 shared gateway adapter 保持通过。

## 边界

本适配器不调用模型、不读取 Key、不上传素材、不下载或解析视频、不启动服务、不登记执行 run，不改变 consent、provider gateway、approval、review 或发布语义。`material-manifest.v1` 只是本地可验证的 metadata/reference envelope。
