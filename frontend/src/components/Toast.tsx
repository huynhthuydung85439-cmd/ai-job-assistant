import type { ToastState } from "../types";
import { Icon } from "./Icon";

export function Toast({ toast }: { toast: ToastState }) {
  return <div className={`toast ${toast.type}`}><Icon name={toast.type === "success" ? "check" : "close"} size={17} />{toast.message}</div>;
}
