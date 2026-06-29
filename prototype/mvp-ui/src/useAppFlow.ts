import { useCallback, useEffect, useReducer, useRef } from "react";
import { appReducer, initialState } from "./store";
import {
  QUESTION_FLOW,
  detectBuildFeedback,
  detectStyleFeedback,
} from "./mockAgent";
import type { ChatMessage } from "./types";

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

  const startRequirementsFlow = useCallback(async () => {
    await pushAgentMessage(
      "欢迎来到 Agent 工坊 MVP 体验版。\n\n我们将走 3 个阶段：做什么 → 长什么样 → 做出来试试。你只需在左侧聊天，右侧会实时展示每个阶段的成果。",
      500,
    );
    await pushAgentMessage(QUESTION_FLOW[0].prompt, 900);
  }, [pushAgentMessage]);

  useEffect(() => {
    if (!bootstrapped.current) {
      bootstrapped.current = true;
      void startRequirementsFlow();
    }
  }, [startRequirementsFlow]);

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

  const sendUserMessage = useCallback(
    async (raw: string) => {
      const text = raw.trim();
      if (!text || stateRef.current.isAgentTyping) return;

      dispatch({
        type: "ADD_MESSAGE",
        message: createMessage("user", text),
      });

      const current = stateRef.current;

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
            "需求已整理完成。请查看右侧《需求文档》，确认无误后点击底部「确认需求，继续」。",
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
            "你可以试试说：「按钮再大一点」「颜色更温暖一点」。满意后请点击「确认风格，开始制作」。",
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
      }
    },
    [pushAgentMessage, runBuildSimulation],
  );

  const confirmRequirements = useCallback(async () => {
    dispatch({ type: "CONFIRM_REQUIREMENTS" });
    await pushAgentMessage(
      "需求已锁定。接下来我会准备 2 套界面风格，你不用懂技术，只需选你喜欢的样子。",
      600,
    );
    await pushAgentMessage(
      "右侧是风格 A「简洁办公」和风格 B「温暖亲和」。你也可以直接在聊天里反馈修改。",
      900,
    );
    dispatch({ type: "SET_PENDING_GATE", gate: "style" });
  }, [pushAgentMessage]);

  const selectStyle = useCallback((styleId: "A" | "B") => {
    dispatch({ type: "SELECT_STYLE", styleId });
  }, []);

  const confirmStyle = useCallback(async () => {
    dispatch({ type: "CONFIRM_STYLE" });
    await pushAgentMessage("风格已确认。我现在开始自动制作，请稍等片刻…", 600);
    await runBuildSimulation();
  }, [pushAgentMessage, runBuildSimulation]);

  const completeProject = useCallback(async () => {
    dispatch({ type: "COMPLETE_PROJECT" });
    await pushAgentMessage(
      "太好了，项目第一版验收通过。\n\n在完整版里，这里会进入「部署测试环境 → 你决定是否上线」。MVP 体验到此完成。",
      700,
    );
  }, [pushAgentMessage]);

  const resetDemo = useCallback(async () => {
    dispatch({ type: "RESET_DEMO" });
    bootstrapped.current = false;
    bootstrapped.current = true;
    await startRequirementsFlow();
  }, [startRequirementsFlow]);

  const currentQuestion = QUESTION_FLOW[state.questionIndex];

  return {
    state,
    currentQuestion,
    sendUserMessage,
    confirmRequirements,
    selectStyle,
    confirmStyle,
    completeProject,
    resetDemo,
    dispatch,
  };
}
