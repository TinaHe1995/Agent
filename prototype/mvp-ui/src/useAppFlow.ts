import { useCallback, useEffect, useReducer, useRef } from "react";
import { appReducer, initialState } from "./store";
import {
  DISCOVERY_FLOW,
  QUESTION_FLOW,
  detectBuildFeedback,
  detectStyleFeedback,
} from "./mockAgent";
import type { ChatMessage, PathChoice, TechChoice } from "./types";

function createMessage(role: ChatMessage["role"], content: string): ChatMessage {
  return {
    id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    role,
    content,
    timestamp: Date.now(),
  };
}

function delay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export function useAppFlow() {
  const [state, dispatch] = useReducer(appReducer, initialState);
  const stateRef = useRef(state);
  stateRef.current = state;
  const bootstrapped = useRef(false);

  const pushAgentMessage = useCallback(async (content: string, pause = 700) => {
    dispatch({ type: "SET_AGENT_TYPING", value: true });
    await delay(pause);
    dispatch({
      type: "ADD_MESSAGE",
      message: createMessage("agent", content),
    });
    dispatch({ type: "SET_AGENT_TYPING", value: false });
  }, []);

  const startDiscoveryFlow = useCallback(async () => {
    await pushAgentMessage(
      "欢迎来到 Agent 工坊体验版。\n\n在动手做软件之前，我们先判断：这个问题值不值得自己做、有没有更省事的路。左侧聊天，右侧看对比。",
      500,
    );
    await pushAgentMessage(DISCOVERY_FLOW[0].prompt, 900);
  }, [pushAgentMessage]);

  const startRequirementsFlow = useCallback(async () => {
    await pushAgentMessage(
      "好，我们按自研来做。我会通过几轮对话把需求整理到右侧，你随时可以改；觉得够了再确认。",
      500,
    );
    await pushAgentMessage(QUESTION_FLOW[0].prompt, 900);
  }, [pushAgentMessage]);

  useEffect(() => {
    if (!bootstrapped.current) {
      bootstrapped.current = true;
      void startDiscoveryFlow();
    }
  }, [startDiscoveryFlow]);

  const runBuildSimulation = useCallback(async () => {
    dispatch({ type: "SET_BUILD_PROGRESS", value: 12 });
    await delay(700);
    dispatch({ type: "SET_BUILD_PROGRESS", value: 38 });
    await pushAgentMessage("已开始制作。右侧会显示进度，完成后可直接试用。", 500);
    await delay(900);
    dispatch({ type: "SET_BUILD_PROGRESS", value: 72 });
    await delay(900);
    dispatch({ type: "SET_BUILD_PROGRESS", value: 100 });
    dispatch({ type: "SET_BUILD_DONE" });
    await pushAgentMessage(
      "第一版已做好。请在右侧实际操作预览，并对照验收清单检查。",
      700,
    );
  }, [pushAgentMessage]);

  const runStagingSimulation = useCallback(async () => {
    dispatch({ type: "SET_STAGING_PROGRESS", value: 20 });
    await delay(500);
    dispatch({ type: "SET_STAGING_PROGRESS", value: 55 });
    await delay(500);
    dispatch({ type: "SET_STAGING_PROGRESS", value: 85 });
    await delay(500);
    dispatch({ type: "SET_STAGING_READY" });
    await pushAgentMessage(
      "测试环境已就绪。请打开右侧链接自测，勾选「上线检查」后决定是否正式上线。",
      700,
    );
  }, [pushAgentMessage]);

  const sendUserMessage = useCallback(
    async (raw: string) => {
      const text = raw.trim();
      if (!text || stateRef.current.isAgentTyping) return;

      dispatch({
        type: "ADD_MESSAGE",
        message: createMessage("user", text),
      });

      const current = stateRef.current;

      if (current.stage === 0 && !current.discoveryReady) {
        const step = DISCOVERY_FLOW[current.questionIndex];
        if (!step) return;

        const snippet = step.applyAnswer(text);
        const brief = current.discoveryBrief
          ? `${current.discoveryBrief}\n${snippet}`
          : snippet;
        dispatch({ type: "UPDATE_DISCOVERY", brief });

        const nextIndex = current.questionIndex + 1;
        if (nextIndex < DISCOVERY_FLOW.length) {
          dispatch({ type: "NEXT_QUESTION" });
          await pushAgentMessage(DISCOVERY_FLOW[nextIndex].prompt);
        } else {
          dispatch({ type: "SET_DISCOVERY_READY" });
          await pushAgentMessage(
            "信息够了。请在右侧「方案对比」里选一条路，选好后在底部确认。",
            900,
          );
        }
        return;
      }

      if (current.stage === 0 && current.discoveryReady && !current.pathEndedBuy) {
        await pushAgentMessage(
          "路线选择请在右侧完成。选好方案后，点底部「确认」即可继续。",
        );
        return;
      }

      if (current.stage === 1 && !current.requirementsComplete) {
        const step = QUESTION_FLOW[current.questionIndex];
        if (!step) return;

        const patch = step.applyAnswer(text, current.requirements);
        dispatch({ type: "UPDATE_REQUIREMENTS", patch });

        const nextIndex = current.questionIndex + 1;
        if (nextIndex < QUESTION_FLOW.length) {
          dispatch({ type: "NEXT_QUESTION" });
          await pushAgentMessage(QUESTION_FLOW[nextIndex].prompt);
        } else {
          dispatch({ type: "SET_REQUIREMENTS_COMPLETE" });
          await pushAgentMessage(
            "需求已整理完成。请查看右侧文档，确认无误后点击底部「确认需求，继续」。",
            900,
          );
        }
        return;
      }

      if (current.stage === 1 && current.requirementsComplete && !current.requirementsConfirmed) {
        dispatch({ type: "UPDATE_REQUIREMENTS", patch: { goal: text } });
        await pushAgentMessage("已根据你的反馈更新需求文档。请再次查看右侧并确认。");
        return;
      }

      if (current.stage === 2 && !current.styleConfirmed) {
        const feedback = detectStyleFeedback(text);
        if (feedback) {
          dispatch({
            type: "ADJUST_STYLE",
            warmth: feedback.warmth,
            buttonSize: feedback.buttonSize,
          });
          await pushAgentMessage(feedback.reply);
        } else {
          await pushAgentMessage(
            "你可以试试说：「按钮再大一点」「颜色更温暖一点」。选好技术路线和风格后，请点击「确认，开始制作」。",
          );
        }
        return;
      }

      if (current.stage === 3) {
        const feedback = detectBuildFeedback(text);
        if (feedback) {
          await pushAgentMessage(feedback, 500);
          dispatch({ type: "REQUEST_CHANGES" });
          await runBuildSimulation();
        } else {
          await pushAgentMessage(
            "请具体说说哪里需要改，例如「手机端打不开」或「导出字段顺序不对」。",
          );
        }
        return;
      }

      if (current.stage === 4 && !current.projectCompleted) {
        await pushAgentMessage(
          "上线前请在右侧完成测试和检查清单。准备好后点底部「上线正式环境」。",
        );
      }
    },
    [pushAgentMessage, runBuildSimulation],
  );

  const selectPath = useCallback((choice: PathChoice) => {
    if (choice) {
      dispatch({ type: "SELECT_PATH", choice });
    }
  }, []);

  const confirmPathSelfBuild = useCallback(async () => {
    dispatch({ type: "CONFIRM_PATH_SELF_BUILD" });
    await startRequirementsFlow();
  }, [startRequirementsFlow]);

  const confirmPathBuy = useCallback(async () => {
    dispatch({ type: "CONFIRM_PATH_BUY" });
    await pushAgentMessage(
      "已记录你选的外部方案。右侧有实施建议和下一步说明；若之后想改成自研，可点「重新开始」。",
      600,
    );
  }, [pushAgentMessage]);

  const confirmRequirements = useCallback(async () => {
    dispatch({ type: "CONFIRM_REQUIREMENTS" });
    await pushAgentMessage(
      "需求已锁定。请在右侧「技术路线」和「选风格」里各选一项，也可以在聊天里微调风格。",
      600,
    );
    dispatch({ type: "SET_PENDING_GATE", gate: "style" });
  }, [pushAgentMessage]);

  const selectTech = useCallback((techId: TechChoice) => {
    if (techId) {
      dispatch({ type: "SELECT_TECH", techId });
    }
  }, []);

  const selectStyle = useCallback((styleId: "A" | "B") => {
    dispatch({ type: "SELECT_STYLE", styleId });
  }, []);

  const confirmStyle = useCallback(async () => {
    dispatch({ type: "CONFIRM_STYLE" });
    await pushAgentMessage("技术路线和风格已确认。我现在开始自动制作，请稍等片刻…", 600);
    await runBuildSimulation();
  }, [pushAgentMessage, runBuildSimulation]);

  const completeAcceptance = useCallback(async () => {
    dispatch({ type: "COMPLETE_ACCEPTANCE" });
    await pushAgentMessage(
      "验收通过。接下来我会部署到测试环境，你在右侧确认后再决定是否正式上线。",
      600,
    );
    await runStagingSimulation();
  }, [pushAgentMessage, runStagingSimulation]);

  const confirmGoLive = useCallback(async () => {
    dispatch({ type: "COMPLETE_GO_LIVE" });
    await pushAgentMessage(
      "已上线正式环境。右侧可复制正式地址和交付物清单。若要改需求或换风格，随时在对话里说，我们按迭代节奏继续。",
      700,
    );
  }, [pushAgentMessage]);

  const pauseProject = useCallback(async () => {
    await pushAgentMessage(
      "好的，测试环境会保持可用。一周后再决定是否上线，或继续在对话里提出修改。",
    );
  }, [pushAgentMessage]);

  const resetDemo = useCallback(async () => {
    dispatch({ type: "RESET_DEMO" });
    bootstrapped.current = false;
    bootstrapped.current = true;
    await startDiscoveryFlow();
  }, [startDiscoveryFlow]);

  const currentQuestion =
    state.stage === 1 ? QUESTION_FLOW[state.questionIndex] : undefined;

  const currentDiscoveryStep =
    state.stage === 0 ? DISCOVERY_FLOW[state.questionIndex] : undefined;

  return {
    state,
    currentQuestion,
    currentDiscoveryStep,
    sendUserMessage,
    selectPath,
    confirmPathSelfBuild,
    confirmPathBuy,
    confirmRequirements,
    selectTech,
    selectStyle,
    confirmStyle,
    completeAcceptance,
    confirmGoLive,
    pauseProject,
    resetDemo,
    dispatch,
  };
}
