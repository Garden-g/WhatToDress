import { Loader2, UploadCloud, X } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { api } from "../api/client";
import type { VisionProvider, WardrobeItem } from "../types";

interface UploadModalProps {
  open: boolean;
  onClose: () => void;
  onUploaded: () => Promise<void>;
}

interface UploadFormState {
  name: string;
  category: string;
  subcategory: string;
  closet_section: WardrobeItem["closet_section"];
  color: string;
  season_tags: string;
  style_tags: string;
  formality: WardrobeItem["formality"];
}

function buildFormState(item: WardrobeItem): UploadFormState {
  return {
    name: item.name ?? "",
    category: item.category,
    subcategory: item.subcategory ?? "",
    closet_section: item.closet_section,
    color: item.color,
    season_tags: item.season_tags.join(", "),
    style_tags: item.style_tags.join(", "),
    formality: item.formality
  };
}

export function UploadModal({ open, onClose, onUploaded }: UploadModalProps) {
  const [file, setFile] = useState<File | null>(null);
  const [draft, setDraft] = useState<WardrobeItem | null>(null);
  const [form, setForm] = useState<UploadFormState | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isConfirming, setIsConfirming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [visionProvider, setVisionProvider] = useState<VisionProvider>("gemini");

  const previewUrl = useMemo(() => {
    if (!file) {
      return "";
    }
    return URL.createObjectURL(file);
  }, [file]);

  useEffect(() => {
    if (!open) {
      setFile(null);
      setDraft(null);
      setForm(null);
      setIsUploading(false);
      setIsConfirming(false);
      setError(null);
      setVisionProvider("gemini");
    }
  }, [open]);

  useEffect(() => {
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [previewUrl]);

  if (!open) {
    return null;
  }

  async function handleUpload() {
    if (!file) {
      setError("先选择一张衣物图片。");
      return;
    }

    try {
      setError(null);
      setIsUploading(true);
      const response = await api.uploadWardrobeItem(file, visionProvider);
      setDraft(response.item);
      setForm(buildFormState(response.item));
    } catch (uploadError) {
      setError(uploadError instanceof Error ? uploadError.message : "上传失败");
    } finally {
      setIsUploading(false);
    }
  }

  async function handleConfirm() {
    if (!draft || !form) {
      return;
    }

    try {
      setError(null);
      setIsConfirming(true);
      await api.confirmWardrobeItem(draft.item_id, {
        name: form.name,
        category: form.category,
        subcategory: form.subcategory,
        closet_section: form.closet_section,
        color: form.color,
        season_tags: form.season_tags
          .split(",")
          .map((tag) => tag.trim())
          .filter(Boolean),
        style_tags: form.style_tags
          .split(",")
          .map((tag) => tag.trim())
          .filter(Boolean),
        formality: form.formality
      });
      await onUploaded();
    } catch (confirmError) {
      setError(confirmError instanceof Error ? confirmError.message : "确认入库失败");
    } finally {
      setIsConfirming(false);
    }
  }

  return (
    <div className="fixed inset-0 z-[100] bg-[rgba(44,36,29,0.38)] backdrop-blur-sm p-4 overflow-y-auto">
      <div className="max-w-4xl mx-auto mt-8 bg-[rgba(251,247,241,0.98)] rounded-[2rem] border border-[color:var(--line)] shadow-2xl overflow-hidden">
        <div className="flex items-center justify-between px-6 py-4 border-b border-[color:var(--line)]">
          <div>
            <h2 className="text-xl font-bold">拍照入库</h2>
            <p className="text-sm text-[color:var(--muted)]">先识别，再让你确认，不直接偷偷入库。</p>
          </div>
          <button
            onClick={onClose}
            className="w-10 h-10 inline-flex items-center justify-center rounded-full hover:bg-[rgba(157,111,61,0.08)]"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="grid lg:grid-cols-[1.1fr_1.2fr] gap-0">
          <div className="p-6 border-b lg:border-b-0 lg:border-r border-[color:var(--line)] space-y-4">
            <label className="block border-2 border-dashed border-[rgba(157,111,61,0.22)] rounded-[1.5rem] p-8 text-center cursor-pointer bg-[rgba(157,111,61,0.04)]">
              <UploadCloud className="w-10 h-10 mx-auto mb-4 text-[color:var(--accent)]" />
              <p className="font-semibold">选择一张衣物照片</p>
              <p className="text-sm text-[color:var(--muted)] mt-2">建议正面、光线清晰，便于识别颜色和轮廓。</p>
              <input
                type="file"
                accept="image/*"
                className="hidden"
                onChange={(event) => setFile(event.target.files?.[0] ?? null)}
              />
            </label>

            <div className="rounded-[1.5rem] overflow-hidden border border-[color:var(--line)] bg-white min-h-[320px]">
              {previewUrl ? (
                <img src={previewUrl} alt="预览图" className="w-full h-full object-cover min-h-[320px]" />
              ) : (
                <div className="min-h-[320px] flex items-center justify-center text-[color:var(--muted)]">
                  这里会显示你刚选的图片
                </div>
              )}
            </div>

            <label className="block text-sm font-semibold text-[color:var(--ink)]">
              识图模型
              <select
                value={visionProvider}
                onChange={(event) => setVisionProvider(event.target.value as VisionProvider)}
                className="mt-2 w-full rounded-xl border border-[color:var(--line)] px-3 py-2 bg-white"
              >
                <option value="gemini">Gemini</option>
                <option value="glm">GLM-4.6V</option>
              </select>
            </label>

            <button
              onClick={() => void handleUpload()}
              disabled={!file || isUploading}
              className="w-full py-3 rounded-2xl bg-[color:rgba(44,36,29,0.95)] text-white font-bold disabled:opacity-50 inline-flex items-center justify-center gap-2"
            >
              {isUploading ? <Loader2 className="w-4 h-4 animate-spin" /> : <UploadCloud className="w-4 h-4" />}
              {isUploading ? `${visionProvider === "gemini" ? "Gemini" : "GLM-4.6V"} 识别中...` : "开始识别"}
            </button>
          </div>

          <div className="p-6 space-y-4">
            <div className="rounded-[1.5rem] border border-[color:var(--line)] bg-white/70 p-4">
              <h3 className="font-bold mb-3">识别结果确认</h3>
              {!draft || !form ? (
                <p className="text-sm text-[color:var(--muted)]">上传并识别完成后，这里会出现待确认属性。</p>
              ) : (
                <div className="grid sm:grid-cols-2 gap-4">
                  <label className="space-y-2 text-sm">
                    <span>名称</span>
                    <input
                      value={form.name}
                      onChange={(event) => setForm({ ...form, name: event.target.value })}
                      className="w-full rounded-xl border border-[color:var(--line)] px-3 py-2 bg-white"
                    />
                  </label>
                  <label className="space-y-2 text-sm">
                    <span>分类</span>
                    <input
                      value={form.category}
                      onChange={(event) => setForm({ ...form, category: event.target.value })}
                      className="w-full rounded-xl border border-[color:var(--line)] px-3 py-2 bg-white"
                    />
                  </label>
                  <label className="space-y-2 text-sm">
                    <span>子分类</span>
                    <input
                      value={form.subcategory}
                      onChange={(event) => setForm({ ...form, subcategory: event.target.value })}
                      className="w-full rounded-xl border border-[color:var(--line)] px-3 py-2 bg-white"
                    />
                  </label>
                  <label className="space-y-2 text-sm">
                    <span>挂放区域</span>
                    <select
                      value={form.closet_section}
                      onChange={(event) =>
                        setForm({
                          ...form,
                          closet_section: event.target.value as WardrobeItem["closet_section"]
                        })
                      }
                      className="w-full rounded-xl border border-[color:var(--line)] px-3 py-2 bg-white"
                    >
                      <option value="top">上装</option>
                      <option value="outerwear">外套</option>
                      <option value="bottom">下装</option>
                      <option value="shoes">鞋</option>
                      <option value="accessory">配件</option>
                      <option value="other">其他</option>
                    </select>
                  </label>
                  <label className="space-y-2 text-sm">
                    <span>颜色</span>
                    <input
                      value={form.color}
                      onChange={(event) => setForm({ ...form, color: event.target.value })}
                      className="w-full rounded-xl border border-[color:var(--line)] px-3 py-2 bg-white"
                    />
                  </label>
                  <label className="space-y-2 text-sm">
                    <span>正式度</span>
                    <select
                      value={form.formality}
                      onChange={(event) =>
                        setForm({
                          ...form,
                          formality: event.target.value as WardrobeItem["formality"]
                        })
                      }
                      className="w-full rounded-xl border border-[color:var(--line)] px-3 py-2 bg-white"
                    >
                      <option value="casual">casual</option>
                      <option value="smart_casual">smart_casual</option>
                      <option value="formal">formal</option>
                    </select>
                  </label>
                  <label className="space-y-2 text-sm sm:col-span-2">
                    <span>季节标签（逗号分隔）</span>
                    <input
                      value={form.season_tags}
                      onChange={(event) => setForm({ ...form, season_tags: event.target.value })}
                      className="w-full rounded-xl border border-[color:var(--line)] px-3 py-2 bg-white"
                    />
                  </label>
                  <label className="space-y-2 text-sm sm:col-span-2">
                    <span>风格标签（逗号分隔）</span>
                    <input
                      value={form.style_tags}
                      onChange={(event) => setForm({ ...form, style_tags: event.target.value })}
                      className="w-full rounded-xl border border-[color:var(--line)] px-3 py-2 bg-white"
                    />
                  </label>
                </div>
              )}
            </div>

            {draft?.analysis_notes && (
              <div className="rounded-[1.25rem] bg-[rgba(157,111,61,0.08)] border border-[color:var(--line)] p-4 text-sm text-[color:var(--ink)]">
                识别备注：{draft.analysis_notes}
              </div>
            )}

            {error && (
              <div className="rounded-[1.25rem] bg-red-50 border border-red-200 p-4 text-sm text-red-700">{error}</div>
            )}

            <button
              onClick={() => void handleConfirm()}
              disabled={!draft || !form || isConfirming}
              className="w-full py-3 rounded-2xl bg-[color:var(--accent)] text-white font-bold disabled:opacity-50 inline-flex items-center justify-center gap-2"
            >
              {isConfirming ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
              {isConfirming ? "确认入库中..." : "确认入库"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
