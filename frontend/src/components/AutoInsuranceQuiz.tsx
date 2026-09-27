"use client";

import { useEffect, useState } from "react";

import { getAutoInsuranceQuiz } from "@/lib/api";
import type { QuizResponse } from "@/lib/types";

export function AutoInsuranceQuiz() {
  const [quiz, setQuiz] = useState<QuizResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [index, setIndex] = useState(0);
  const [selected, setSelected] = useState<number | null>(null);
  const [score, setScore] = useState(0);
  const [finished, setFinished] = useState(false);

  useEffect(() => {
    getAutoInsuranceQuiz()
      .then(setQuiz)
      .catch(() => setError("Could not load the quiz right now."));
  }, []);

  const restart = () => {
    setIndex(0);
    setSelected(null);
    setScore(0);
    setFinished(false);
  };

  const choose = (optionIndex: number) => {
    if (selected !== null || !quiz) return;
    setSelected(optionIndex);
    if (optionIndex === quiz.questions[index].correct_index) {
      setScore((current) => current + 1);
    }
  };

  const next = () => {
    if (!quiz) return;
    if (index + 1 >= quiz.questions.length) {
      setFinished(true);
      return;
    }
    setIndex((current) => current + 1);
    setSelected(null);
  };

  if (error) {
    return <div className="rounded-xl border border-danger/30 bg-danger/10 p-3 text-xs text-danger">{error}</div>;
  }

  if (!quiz) {
    return <div className="p-4 text-xs text-muted">Loading quiz...</div>;
  }

  if (finished) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-3 p-6 text-center">
        <p className="text-xs uppercase tracking-[0.25em] text-muted">Quiz complete</p>
        <p className="text-3xl font-semibold text-text">
          {score} / {quiz.questions.length}
        </p>
        <p className="max-w-xs text-sm text-muted">
          {score === quiz.questions.length
            ? "Perfect score - you know your auto coverage."
            : "Review the explanations above for anything you missed, then try again."}
        </p>
        <button type="button" onClick={restart} className="mt-2 rounded-full bg-accent px-4 py-2 text-sm font-medium text-background transition hover:opacity-90">
          Retake quiz
        </button>
      </div>
    );
  }

  const question = quiz.questions[index];

  return (
    <div className="flex flex-1 flex-col overflow-y-auto p-4">
      {index === 0 ? <p className="text-sm text-text">Storms don&apos;t just threaten your home - here&apos;s what your auto policy actually covers when one hits.</p> : null}
      <p className="mt-1 text-[11px] text-muted">{quiz.disclaimer}</p>
      <div className="mt-3 flex items-center justify-between text-[11px] uppercase tracking-[0.2em] text-muted">
        <span>
          Question {index + 1} of {quiz.questions.length}
        </span>
        <span>Score {score}</span>
      </div>
      <p className="mt-3 text-sm font-medium text-text">{question.question}</p>

      <div className="mt-3 space-y-2">
        {question.options.map((option, optionIndex) => {
          const isCorrect = optionIndex === question.correct_index;
          const isChosen = optionIndex === selected;
          const revealed = selected !== null;
          let tone = "border-border bg-background text-text hover:border-accent";
          if (revealed && isCorrect) tone = "border-success/50 bg-success/10 text-text";
          else if (revealed && isChosen && !isCorrect) tone = "border-danger/50 bg-danger/10 text-text";

          return (
            <button
              key={option}
              type="button"
              onClick={() => choose(optionIndex)}
              disabled={revealed}
              className={`w-full rounded-2xl border p-3 text-left text-sm transition ${tone} disabled:cursor-default`}
            >
              {option}
            </button>
          );
        })}
      </div>

      {selected !== null ? (
        <div className="mt-3 rounded-2xl border border-border bg-background p-3 text-xs text-muted">
          <p className="text-text">{question.explanation}</p>
          <p className="mt-2 text-[11px] uppercase tracking-[0.15em] text-muted/80">Source: {question.source}</p>
          <button type="button" onClick={next} className="mt-3 rounded-full bg-accent px-4 py-1.5 text-xs font-medium text-background transition hover:opacity-90">
            {index + 1 >= quiz.questions.length ? "See results" : "Next question"}
          </button>
        </div>
      ) : null}
    </div>
  );
}
