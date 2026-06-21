import { useRef } from "react";
import gsap from "gsap";
import { useGSAP } from "@gsap/react";
import { useReducedMotion } from "./useReducedMotion";

gsap.registerPlugin(useGSAP);

export function useGsapReveal({
  selector = "children",
  y = 14,
  x = 0,
  duration = 0.42,
  stagger = 0.055,
  delay = 0,
  dependencies = [],
} = {}) {
  const scope = useRef(null);
  const reducedMotion = useReducedMotion();

  useGSAP(
    () => {
      const root = scope.current;
      if (!root) return;

      const targets =
        selector === "self"
          ? [root]
          : selector === "children"
            ? Array.from(root.children)
            : Array.from(root.querySelectorAll(selector));

      if (!targets.length) return;

      if (reducedMotion) {
        gsap.set(targets, { autoAlpha: 1, x: 0, y: 0, clearProps: "transform" });
        return;
      }

      gsap.fromTo(
        targets,
        { autoAlpha: 0, x, y },
        {
          autoAlpha: 1,
          x: 0,
          y: 0,
          duration,
          stagger,
          delay,
          ease: "power2.out",
          clearProps: "transform",
        },
      );
    },
    { scope, dependencies: [reducedMotion, ...dependencies], revertOnUpdate: true },
  );

  return scope;
}
