贡献指南
========

我们欢迎所有形式的贡献！无论是bug报告、功能建议、文档改进还是代码贡献。

贡献类型
--------

1. **代码贡献**
   ~~~~~~~~~

   * 修复bug
   * 添加新功能
   * 性能优化
   * 代码重构

2. **文档贡献**
   ~~~~~~~~~

   * 改进用户指南
   * 完善API文档
   * 添加使用示例
   * 翻译文档

3. **测试贡献**
   ~~~~~~~~~

   * 添加单元测试
   * 增加集成测试
   * 性能测试
   * 端到端测试

4. **问题反馈**
   ~~~~~~~~~

   * 报告bug
   * 功能请求
   * 性能问题
   * 使用问题

5. **其他贡献**
   ~~~~~~~~~

   * 代码审查
   * 社区支持
   * 设计建议

开发流程
--------

1. **准备工作**
   ~~~~~~~~~

   * Fork项目仓库
   * 克隆到本地
   * 设置开发环境
   * 创建功能分支

2. **开发实现**
   ~~~~~~~~~

   * 编写代码
   * 编写测试
   * 更新文档
   * 确保代码质量

3. **提交代码**
   ~~~~~~~~~

   * 提交Pull Request
   * 填写PR模板
   * 响应代码审查
   * 修复反馈问题

4. **合并代码**
   ~~~~~~~~~

   * 通过所有检查
   * 获得批准
   * 合并到主分支
   * 部署到生产

详细步骤
--------

1. Fork和Clone
~~~~~~~~~~~~~~

.. code-block:: bash

   # 1. 在GitHub上Fork项目
   # 访问: https://github.com/org/quant-system

   # 2. 克隆到本地
   git clone https://github.com/YOUR_USERNAME/quant-system.git
   cd quant-system

   # 3. 添加上游仓库
   git remote add upstream https://github.com/org/quant-system.git

   # 4. 创建开发分支
   git checkout -b feature/your-feature-name

2. 设置开发环境
~~~~~~~~~~~~~~

.. code-block:: bash

   # 安装依赖
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   # 或 .venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   pip install -r test_requirements.txt
   pip install -r docs_requirements.txt

   # 安装pre-commit钩子
   pip install pre-commit
   pre-commit install

   # 创建配置文件
   cp .env.example .env
   # 编辑 .env，填入必要的API密钥

3. 开发代码
~~~~~~~~~

   **代码规范检查**

   .. code-block:: bash

      # 格式化代码
      black src/ tests/

      # 排序导入
      isort src/ tests/

      # 代码风格检查
      flake8 src/ tests/

      # 类型检查
      mypy src/

   **运行测试**

   .. code-block:: bash

      # 运行所有测试
      pytest tests/ -v

      # 生成覆盖率报告
      pytest tests/ --cov=src --cov-report=html

      # 运行特定测试
      pytest tests/unit/test_strategies/test_kdj.py -v

4. 提交更改
~~~~~~~~~

   **选择更改类型**

   按照约定式提交格式：

   .. code-block:: text

      feat(backtest): 添加MACD策略实现

      新增MACD技术指标策略，支持：
      - 快速线和慢速线计算
      - 信号线交叉检测
      - 参数优化功能

      Closes #123

   **提交命令**

   .. code-block:: bash

      # 添加文件
      git add .

      # 提交更改
      git commit -m "feat(backtest): 添加MACD策略实现

      新增MACD技术指标策略，支持：
      - 快速线和慢速线计算
      - 信号线交叉检测
      - 参数优化功能

      Closes #123"

      # 推送到GitHub
      git push origin feature/your-feature-name

5. 创建Pull Request
~~~~~~~~~~~~~~~~~

   **在GitHub上创建PR**

   访问你的Fork仓库，点击"New Pull Request"

   **PR标题和描述**

   .. code-block:: text

      标题: feat(backtest): 添加MACD策略实现

      描述:
      ## 更改说明
      本PR添加了MACD（指数平滑异同移动平均）技术指标策略。

      ## 新增功能
      - MACD快速线和慢速线计算
      - 信号线生成
      - 金叉死叉信号检测
      - 可配置参数（fast, slow, signal周期）

      ## 测试
      - 添加了单元测试
      - 验证了各种市场条件下的表现
      - 包含边界情况测试

      ## 文档
      - 更新了API文档
      - 添加了使用示例
      - 更新了策略列表

      ## 兼容性
      - 向后兼容
      - 不破坏现有API
      - 添加了弃用警告（如需要）

   **PR模板**

   创建 `.github/pull_request_template.md`:

   .. code-block:: markdown

      ## 更改类型
      - [ ] Bug修复 (向后兼容的bug修复)
      - [ ] 新功能 (向后兼容的新功能)
      - [ ] 重大更改 (会破坏现有功能的更改)
      - [ ] 文档改进
      - [ ] 重构
      - [ ] 性能改进
      - [ ] 测试

      ## 更改说明
      <!-- 详细描述此次更改 -->

      ## 测试
      <!-- 描述如何测试此更改 -->
      - [ ] 我已经添加了测试来覆盖我的更改
      - [ ] 所有新的和现有的测试都通过了
      - [ ] 我已经手动测试了此更改

      ## 检查清单
      - [ ] 我的代码遵循了项目的代码规范
      - [ ] 我已经进行了自我代码审查
      - [ ] 我的更改生成了新的警告
      - [ ] 我已经添加了必要的注释，特别是在难以理解的区域
      - [ ] 我已经对相应的文档进行了更改
      - [ ] 我的更改不会引入新的依赖关系

      ## 截图（如果适用）
      <!-- 添加相关截图 -->

      ## 相关问题
      Closes #issue_number

代码审查
--------

**作为贡献者**

1. **响应审查意见**
   ~~~~~~~~~~~~

   * 及时回复评论
   * 解释你的设计决策
   * 根据建议进行修改
   * 保持专业和礼貌

2. **主动沟通**
   ~~~~~~~~~~

   * 在PR中描述清楚实现
   * 解释复杂逻辑
   * 提前讨论大更改
   * 寻求早期反馈

**作为审查者**

1. **审查标准**
   ~~~~~~~~~~

   * 代码质量和风格
   * 测试覆盖率
   * 文档完整性
   * 性能影响
   * 安全性

2. **审查流程**
   ~~~~~~~~~~

   * 理解更改意图
   * 检查实现细节
   * 运行测试
   * 提出建设性意见
   * 最终批准或请求更改

代码规范
--------

所有贡献必须遵循项目规范：

1. **代码风格**
   ~~~~~~~~~~

   * 使用 black 格式化
   * 遵循 PEP 8
   * 使用类型提示
   * 编写清晰注释

2. **测试要求**
   ~~~~~~~~~~

   * 新功能必须有测试
   * Bug修复需要回归测试
   * 测试覆盖率 ≥ 80%
   * 核心模块覆盖率 ≥ 90%

3. **文档要求**
   ~~~~~~~~~~

   * 所有公共API必须有docstring
   * 复杂逻辑需要注释
   * 新功能需要更新文档
   - 保持README更新

错误报告
--------

**提交Bug报告**

使用GitHub Issues，模板：

.. code-block:: markdown

   **Bug描述**
   <!-- 简要描述bug -->

   **复现步骤**
   1. 前往 '...'
   2. 点击 '....'
   3. 滚动到 '....'
   4. 看到错误

   **期望行为**
   <!-- 描述你期望发生什么 -->

   **实际行为**
   <!-- 描述实际发生了什么 -->

   **屏幕截图**
   <!-- 如果适用，添加截图 -->

   **环境信息**
   - OS: [e.g. Windows 11]
   - Python版本: [e.g. 3.11.0]
   - 系统版本: [e.g. 22]

   **附加上下文**
   <!-- 添加任何其他关于问题的上下文 -->

功能请求
--------

**提交功能请求**

.. code-block:: markdown

   **功能描述**
   <!-- 简要描述你希望的功能 -->

   **动机**
   <!-- 解释为什么这个功能有用 -->

   **建议解决方案**
   <!-- 描述你希望如何实现 -->

   **替代方案**
   <!-- 描述你考虑过的任何替代解决方案 -->

   **额外上下文**
   <!-- 添加任何其他关于功能请求的图片或上下文 -->

问题优先级
----------

**严重性等级**

* **P0 - 关键**: 系统崩溃、数据丢失、安全漏洞
* **P1 - 高**: 重要功能不可用
* **P2 - 中**: 一般功能问题
* **P3 - 低**: 小问题、改进建议

**响应时间**

* P0: 24小时内响应
* P1: 3个工作日内响应
* P2: 1周内响应
* P3: 2周内响应

发布流程
--------

1. **版本规划**
   ~~~~~~~~~

   * 确定发布版本号
   * 列出新功能和bug修复
   * 更新CHANGELOG
   * 准备发布说明

2. **预发布**
   ~~~~~~~~

   * 创建发布分支
   * 完整测试
   * 更新版本号
   * 生成发布候选版

3. **正式发布**
   ~~~~~~~~

   * 合并到主分支
   * 创建Git标签
   * 构建发布包
   * 部署到生产

4. **发布后**
   ~~~~~~~~

   * 监控系统
   * 收集反馈
   * 修复紧急问题
   * 计划下一版本

开发最佳实践
------------

1. **小步提交**
   ~~~~~~~~~~

   每次提交只做一个逻辑更改，便于审查和回滚。

2. **提前沟通**
   ~~~~~~~~~~

   在开始大更改前，先创建Issue讨论。

3. **保持主分支稳定**
   ~~~~~~~~~~~~~~~~

   不要在主分支上直接开发，使用功能分支。

4. **及时更新**
   ~~~~~~~~~~

   定期从上游更新，保持分支同步。

.. code-block:: bash

   git fetch upstream
   git rebase upstream/main
   git push origin feature/your-feature

5. **测试驱动开发**
   ~~~~~~~~~~~~~~

   先写测试，再写实现。

6. **持续集成**
   ~~~~~~~~~~

   确保所有检查通过：

   .. code-block:: bash

      # 本地检查
      black --check src/ tests/
      flake8 src/ tests/
      mypy src/
      pytest tests/ -v
      pre-commit run --all-files

社区行为准则
------------

我们致力于营造一个开放、友好的社区环境。

**我们的承诺**

为了促进一个开放和友善的环境，我们作为贡献者和维护者承诺，无论年龄、体型、残疾、种族、性别认同、经验水平、教育、社会经济地位、国籍、个人外表、种族、宗教或性认同和取向，我们都不会骚扰项目的任何参与者。

**我们的标准**

有助于创造积极环境的行为包括：
* 使用友好和包容的语言
* 尊重不同的观点和经验
* 优雅地接受建设性批评
* 关注对社区最有利的事情
* 对其他社区成员表示同理心

不可接受的行为包括：
* 使用性化的语言或图像以及不受欢迎的性关注或追求
* 恶意评论、人身攻击或政治攻击
* 公开或私下的骚扰
* 未经明确许可发布他人的私人信息
* 在专业环境中可能被合理认为不适当的其他行为

**执行**

通过 email (conduct@quant-system.com) 报告违规行为。

资源链接
--------

**文档**

* `GitHub指南 <https://guides.github.com/>`_
* `Git文档 <https://git-scm.com/doc>`_
* `Python开发指南 <https://devguide.python.org/>`_
* `pytest文档 <https://docs.pytest.org/>`_

**工具**

* `GitHub Desktop <https://desktop.github.com/>`_
* `VS Code <https://code.visualstudio.com/>`_
* `GitKraken <https://www.gitkraken.com/>`_

**社区**

* `GitHub Discussions <https://github.com/org/quant-system/discussions>`_
* `Slack频道 <https://quant-system.slack.com>`_
* `邮件列表 <mailto:dev@quant-system.com>`_

致谢
----

感谢所有为项目做出贡献的开发者！你们的贡献让这个项目变得更好。

**贡献者名单**

项目使用 `All Contributors <https://allcontributors.org/>`_ 规范识别所有贡献者：

.. code-block:: markdown

   <!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
   <!-- prettier-ignore-start -->
   <!-- markdownlint-disable -->
   <table>
     <tr>
       <td align="center">
         <a href="https://github.com/username">
           <img src="https://github.com/username.png" width="100px;" alt="Name"/>
           <br/>
           <sub><b>Name</b></sub>
         </a>
         <br/>
         <a href="#code-username" title="Code">💻</a>
       </td>
     </tr>
   </table>
   <!-- markdownlint-restore -->
   <!-- prettier-ignore-end -->
   <!-- ALL-CONTRIBUTORS-LIST:END -->

常见问题
--------

**Q: 我可以在没有分配Issue的情况下创建PR吗？**

A: 可以，但建议先创建一个Issue讨论。

**Q: 多久会审查我的PR？**

A: 通常在3个工作日内，但可能因复杂度而异。

**Q: 我的PR被拒绝了怎么办？**

A: 审查者会提供反馈，可以根据建议修改后重新提交。

**Q: 如何获得"good first issue"标签？**

A: 寻找标记为"good first issue"或"beginner friendly"的Issue。

**Q: 可以同时修复多个问题吗？**

A: 建议每个PR只修复一个问题，除非它们密切相关。

**Q: 如何保持分支同步？**

A: 定期从上游拉取更新：
   .. code-block:: bash
      git fetch upstream
      git rebase upstream/main
