(function() {
	try {
		var e = typeof globalThis < "u" ? globalThis : typeof window < "u" ? window : typeof global < "u" ? global : typeof self < "u" ? self : {}, t = new e.Error().stack;
		t && (e._sentryDebugIds = e._sentryDebugIds || {}, e._sentryDebugIds[t] = "ab33e0b7-cec0-44e2-81d6-6b3751943cd6", e._sentryDebugIdIdentifier = "sentry-dbid-ab33e0b7-cec0-44e2-81d6-6b3751943cd6");
	} catch {}
})();
import { Button as e, Checkbox as t, CollectionSummary as n, DUPLICATES_KEY as r, EmptyState as i, FilterGlass as a, GlassPill as o, KEEP_LABELS as s, LOC as c, MEDIA_SOURCES_KEY as l, MEDIA_SOURCE_ICONS as u, Note as d, SelectionDock as f, SourceLabel as p, SourceMark as m, TRASH_KEY as h, __toESM as g, batchOperate as _, bulkCloudPreferences as ee, busyProps as v, cardClass as y, cloudLocations as b, confirmModal as x, distinctName as S, duplicateVictims as C, errorMessage as w, fetchDuplicates as te, fetchMediaSources as ne, fmtDur as T, fmtSize as E, formatBitrate as D, formatFps as O, formatResolution as k, fullySelectedGroups as A, keepGroup as j, mixedCloudPreferences as M, pruneSelection as N, queryClient as P, require_jsx_runtime as F, require_react as I, selectedBytes as L, sharedNamePrefix as re, spriteGlyph as R, t as z, toggleSelected as B, useMutation as V, useQuery as H, victimBytes as U } from "./peach-app.js";
// src/react/duplicates/duplicates-page.tsx
var W = /* @__PURE__ */ g(I(), 1), G = F(), K = R("play"), q = R("file-stack"), J = y({
	padding: "none",
	radius: "surface",
	className: "mb-6 overflow-hidden dark:bg-background-primary-default"
}), Y = "rounded-sm px-1.5 py-px text-caption-1-regular leading-5", X = "rounded-sm px-2 py-0.5 text-caption-1-regular leading-5", Z = "font-mono text-caption-1-regular leading-5 text-text-secondary", Q = () => {
	P.invalidateQueries({
		queryKey: r,
		exact: !0
	}), P.invalidateQueries({
		queryKey: h,
		exact: !0
	});
};
function ie(e) {
	return e.identical ? /* @__PURE__ */ (0, G.jsx)("span", {
		className: `${X} text-(--keep)`,
		children: z("cleanup:duplicates.sha1Match")
	}) : /* @__PURE__ */ (0, G.jsx)("span", {
		className: `${X} text-text-secondary`,
		children: e.evidence === "same_code_short_copy" ? z("cleanup:duplicates.sameCodeShorter") : z("cleanup:duplicates.byDuration")
	});
}
function ae({ file: e, prefix: n, openItem: r, selected: i, onSelect: a }) {
	let o = () => r(e.id), s = c[e.location] || e.location || e.drive;
	return /* @__PURE__ */ (0, G.jsxs)("div", {
		className: "duplicate-row items-center gap-3 border-t border-separator-border px-5 py-4 max-compact:p-4",
		children: [
			/* @__PURE__ */ (0, G.jsxs)("button", {
				type: "button",
				onClick: o,
				"aria-label": z("cleanup:duplicates.previewFile", { name: e.name }),
				className: "relative row-span-3 inline-grid aspect-16/10 w-full cursor-pointer place-items-center overflow-hidden rounded-2lg bg-background-tertiary-default text-text-secondary",
				children: [/* @__PURE__ */ (0, G.jsx)(K, {
					"aria-hidden": !0,
					className: "size-6"
				}), /* @__PURE__ */ (0, G.jsx)("img", {
					src: `/thumb?id=${e.id}&c=4`,
					alt: "",
					loading: "lazy",
					onError: (e) => e.currentTarget.remove(),
					className: "absolute inset-0 size-full object-contain"
				})]
			}),
			/* @__PURE__ */ (0, G.jsxs)("span", {
				className: "flex min-w-0 items-center gap-2 max-duplicate-narrow:col-start-2 max-duplicate-narrow:-col-end-1",
				children: [
					/* @__PURE__ */ (0, G.jsx)(t, {
						size: "sm",
						className: "flex-none",
						isSelected: i,
						onChange: a,
						"aria-label": z("cleanup:duplicates.selectFile", { name: e.name })
					}),
					/* @__PURE__ */ (0, G.jsx)("button", {
						type: "button",
						onClick: o,
						title: e.name,
						"data-middle-truncate": !0,
						"data-middle-truncate-within": !0,
						className: "min-w-0 shrink cursor-pointer truncate text-left text-body-regular hover:text-text-secondary",
						children: S(e.name, n)
					}),
					e.is_largest || e.is_longest || e.is_highest_bitrate ? /* @__PURE__ */ (0, G.jsxs)("span", {
						className: "flex flex-none gap-1",
						children: [
							e.is_largest ? /* @__PURE__ */ (0, G.jsx)("i", {
								className: `${Y} not-italic bg-background-primary-hover text-text-secondary`,
								children: z("cleanup:duplicates.largest")
							}) : null,
							e.is_longest ? /* @__PURE__ */ (0, G.jsx)("i", {
								className: `${Y} not-italic bg-(--keep)/22 text-(--keep)`,
								children: z("cleanup:duplicates.longest")
							}) : null,
							e.is_highest_bitrate ? /* @__PURE__ */ (0, G.jsx)("i", {
								className: `${Y} not-italic bg-background-primary-hover text-text-secondary`,
								children: z("cleanup:duplicates.highestBitrate")
							}) : null
						]
					}) : null
				]
			}),
			/* @__PURE__ */ (0, G.jsxs)("span", {
				className: `${Z} flex min-w-0 items-center gap-1.5`,
				children: [/* @__PURE__ */ (0, G.jsx)(m, { mark: u[e.location] || "database" }), /* @__PURE__ */ (0, G.jsx)("span", {
					title: s,
					className: "min-w-0 truncate",
					children: s
				})]
			}),
			/* @__PURE__ */ (0, G.jsx)("span", {
				className: Z,
				children: E(e.size || 0)
			}),
			/* @__PURE__ */ (0, G.jsx)("span", {
				className: Z,
				children: T(e.duration)
			}),
			/* @__PURE__ */ (0, G.jsxs)("span", {
				className: `${Z} col-start-2 -col-end-1 flex min-w-0 flex-wrap gap-x-4 gap-y-0.5`,
				children: [
					/* @__PURE__ */ (0, G.jsx)("span", {
						title: z("cleanup:duplicates.resolutionLabel"),
						children: k(e)
					}),
					/* @__PURE__ */ (0, G.jsx)("span", {
						title: z("cleanup:duplicates.bitrateLabel"),
						children: D(e.bitrate)
					}),
					/* @__PURE__ */ (0, G.jsx)("span", {
						title: z("cleanup:duplicates.fpsLabel"),
						children: O(e.fps)
					})
				]
			}),
			/* @__PURE__ */ (0, G.jsx)("span", {
				className: `${Z} col-start-2 -col-end-1 min-w-0 pt-0.5 wrap-anywhere max-duplicate-narrow:col-span-full`,
				children: e.path ?? ""
			})
		]
	});
}
function $({ openItem: t, toast: u, failure: m }) {
	let h = H({
		queryKey: r,
		queryFn: ({ signal: e }) => te(e)
	}), g = H({
		queryKey: l,
		queryFn: ({ signal: e }) => ne(e)
	}), [y, S] = (0, W.useState)(""), [T, D] = (0, W.useState)(/* @__PURE__ */ new Set()), O = h.data?.groups;
	(0, W.useEffect)(() => {
		O && D((e) => N(e, O));
	}, [O]);
	let k = V({
		mutationFn: (e) => _(e, "dispose"),
		onSuccess: (e, t) => {
			Q(), D((e) => new Set([...e].filter((e) => !t.includes(e)))), u(z("cleanup:duplicates.movedToTrash", { count: t.length }), { undo: async () => {
				try {
					await _(t, "restore");
				} catch (e) {
					m(z("cleanup:duplicates.undoTrash"), e);
				} finally {
					Q();
				}
			} });
		},
		onSettled: () => S("")
	}), P = V({
		mutationFn: (e) => j(e.files.map((e) => e.id), !0),
		onSuccess: (e, t) => {
			Q(), u(z("cleanup:duplicates.keptAll", { code: t.code }), { undo: async () => {
				try {
					await j(t.files.map((e) => e.id), !1);
				} catch (e) {
					m(z("cleanup:duplicates.undoKeepAll"), e);
				} finally {
					Q();
				}
			} });
		},
		onError: (e) => m(z("cleanup:duplicates.markKeepAll"), e),
		onSettled: () => S("")
	}), F = h.data;
	if (!F) return /* @__PURE__ */ (0, G.jsx)("div", {
		className: "mx-auto w-full max-w-board",
		children: /* @__PURE__ */ (0, G.jsx)(d, {
			tone: "error",
			title: z("cleanup:duplicates.loadFailed"),
			children: h.error ? w(h.error) : z("cleanup:duplicates.listUnavailable")
		})
	});
	let I = F.groups ?? [], R = b(g.data), K = ({ groups: e, keep: t, key: n }) => {
		if (k.isPending) return;
		let r = C(e, t);
		r.length && x({
			title: z("cleanup:duplicates.moveToTrash"),
			body: z("cleanup:duplicates.trashBody", {
				count: r.length,
				keep: s[t] ?? s.largest,
				size: E(U(e, r))
			}),
			confirmLabel: z("cleanup:duplicates.moveToTrash"),
			onConfirm: () => (S(n), k.mutateAsync(r))
		});
	}, Y = [...T], Z = () => {
		if (k.isPending || !Y.length) return;
		let e = A(I, T), t = E(L(I, T));
		x({
			title: z("cleanup:duplicates.moveToTrash"),
			body: z(e ? "cleanup:duplicates.trashSelectedBodyEmptied" : "cleanup:duplicates.trashSelectedBody", {
				count: Y.length,
				size: t,
				groups: e
			}),
			confirmLabel: z("cleanup:duplicates.moveToTrash"),
			onConfirm: () => (S("selected"), k.mutateAsync(Y))
		});
	}, $ = (e) => v(y === e && (k.isPending || P.isPending)), oe = (e, t) => {
		P.isPending || k.isPending || (S(t), P.mutate(e));
	};
	return /* @__PURE__ */ (0, G.jsxs)("div", {
		className: "mx-auto w-full max-w-board pb-10.5",
		children: [
			/* @__PURE__ */ (0, G.jsx)(n, {
				label: z("cleanup:duplicates.summaryLabel"),
				figure: z("cleanup:duplicates.groupCount", { count: Number(F.total || 0) }),
				detail: z("cleanup:duplicates.summaryDetail", {
					count: Number(F.files || 0),
					size: E(F.reclaimable)
				})
			}),
			I.length ? /* @__PURE__ */ (0, G.jsxs)(a, {
				title: z("cleanup:duplicates.bulkKeep"),
				children: [
					/* @__PURE__ */ (0, G.jsx)(o, {
						busy: y === "all:largest",
						onPress: () => K({
							groups: I,
							keep: "largest",
							key: "all:largest"
						}),
						children: z("cleanup:duplicates.allKeepLargest")
					}),
					/* @__PURE__ */ (0, G.jsx)(o, {
						busy: y === "all:longest",
						onPress: () => K({
							groups: I,
							keep: "longest",
							key: "all:longest"
						}),
						children: z("cleanup:duplicates.allKeepLongest")
					}),
					ee(I, R).map((e) => /* @__PURE__ */ (0, G.jsx)(o, {
						busy: y === `all:${e}`,
						onPress: () => K({
							groups: I,
							keep: e,
							key: `all:${e}`
						}),
						children: /* @__PURE__ */ (0, G.jsx)(p, {
							source: e,
							label: z("cleanup:duplicates.allPreferStorage", { storage: c[e] || e })
						})
					}, e))
				]
			}) : null,
			k.isError ? /* @__PURE__ */ (0, G.jsx)("div", {
				className: "mb-5",
				children: /* @__PURE__ */ (0, G.jsx)(d, {
					tone: "error",
					title: z("cleanup:duplicates.trashFailed"),
					children: w(k.error)
				})
			}) : null,
			I.length ? I.map((n, r) => {
				let i = [n], a = re(n.files.map((e) => e.name)), o = (e) => `${r}:${e}`;
				return /* @__PURE__ */ (0, G.jsxs)("section", {
					"aria-label": n.code,
					className: J,
					children: [/* @__PURE__ */ (0, G.jsxs)("div", {
						className: "flex flex-wrap items-center gap-3 bg-background-tertiary-default p-5 max-compact:p-4 dark:bg-background-secondary-default",
						children: [
							/* @__PURE__ */ (0, G.jsx)("b", {
								className: "text-title-2-medium text-text-primary",
								children: n.code
							}),
							/* @__PURE__ */ (0, G.jsx)("span", {
								className: "font-mono text-caption-1-regular leading-5 text-text-primary",
								children: z("cleanup:duplicates.groupDetail", {
									count: Number(n.count || 0),
									size: E(n.reclaimable)
								})
							}),
							ie(n),
							n.cross_drive ? /* @__PURE__ */ (0, G.jsx)("span", {
								className: `${X} text-text-secondary`,
								children: z("cleanup:duplicates.crossDrive", { drives: n.drives.join(" ") })
							}) : null,
							/* @__PURE__ */ (0, G.jsxs)("span", {
								className: "ml-auto flex flex-wrap gap-2 max-compact:ml-0 max-compact:w-full",
								children: [
									/* @__PURE__ */ (0, G.jsx)(e, {
										variant: "secondary",
										size: "small",
										...$(o("largest")),
										onClick: () => K({
											groups: i,
											keep: "largest",
											key: o("largest")
										}),
										children: z("cleanup:duplicates.keepLargest")
									}),
									/* @__PURE__ */ (0, G.jsx)(e, {
										variant: "secondary",
										size: "small",
										...$(o("longest")),
										onClick: () => K({
											groups: i,
											keep: "longest",
											key: o("longest")
										}),
										children: z("cleanup:duplicates.keepLongest")
									}),
									M(n.files, R).map((t) => /* @__PURE__ */ (0, G.jsx)(e, {
										variant: "secondary",
										size: "small",
										...$(o(t)),
										onClick: () => K({
											groups: i,
											keep: t,
											key: o(t)
										}),
										children: /* @__PURE__ */ (0, G.jsx)(p, {
											source: t,
											label: z("cleanup:duplicates.keepStorage", { storage: c[t] || t })
										})
									}, t)),
									/* @__PURE__ */ (0, G.jsx)(e, {
										variant: "secondary",
										size: "small",
										...$(o("keep")),
										onClick: () => oe(n, o("keep")),
										children: z("cleanup:duplicates.keepAll")
									}),
									/* @__PURE__ */ (0, G.jsx)(e, {
										variant: "danger",
										size: "small",
										...$(o("all")),
										onClick: () => K({
											groups: i,
											keep: "all",
											key: o("all")
										}),
										children: z("cleanup:duplicates.trashGroup")
									})
								]
							})
						]
					}), /* @__PURE__ */ (0, G.jsx)("div", { children: n.files.map((e) => /* @__PURE__ */ (0, G.jsx)(ae, {
						file: e,
						prefix: a,
						openItem: t,
						selected: T.has(e.id),
						onSelect: (t) => D((n) => B(n, e.id, t))
					}, e.id)) })]
				}, `${n.code}-${r}`);
			}) : /* @__PURE__ */ (0, G.jsx)(i, {
				icon: q,
				title: z("cleanup:duplicates.emptyTitle"),
				children: z("cleanup:duplicates.emptyBody")
			}),
			I.length > 0 && F.total > I.length ? /* @__PURE__ */ (0, G.jsx)("p", {
				className: "text-center text-caption-1-regular text-text-secondary",
				children: z("cleanup:duplicates.topGroups", {
					shown: I.length.toLocaleString(),
					count: Number(F.total)
				})
			}) : null,
			/* @__PURE__ */ (0, G.jsxs)(f, {
				label: z("cleanup:duplicates.selectionActions"),
				visible: T.size > 0,
				count: z("cleanup:duplicates.selectedCount", {
					count: T.size,
					size: E(L(I, T))
				}),
				children: [/* @__PURE__ */ (0, G.jsx)(e, {
					variant: "secondary",
					size: "small",
					disabled: k.isPending,
					onClick: () => D(/* @__PURE__ */ new Set()),
					children: z("cleanup:duplicates.clearSelection")
				}), /* @__PURE__ */ (0, G.jsx)(e, {
					variant: "danger",
					size: "small",
					...$("selected"),
					onClick: Z,
					children: z("cleanup:duplicates.moveToTrash")
				})]
			}),
			F.kept ? /* @__PURE__ */ (0, G.jsx)("p", {
				className: "mt-2 text-center text-caption-1-regular text-text-secondary",
				children: z("cleanup:duplicates.keptHidden", { count: F.kept })
			}) : null
		]
	});
}
export { $ as DuplicatesPage };

//# debugId=ab33e0b7-cec0-44e2-81d6-6b3751943cd6