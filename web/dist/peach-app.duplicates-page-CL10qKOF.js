(function() {
	try {
		var e = typeof globalThis < "u" ? globalThis : typeof window < "u" ? window : typeof global < "u" ? global : typeof self < "u" ? self : {}, t = new e.Error().stack;
		t && (e._sentryDebugIds = e._sentryDebugIds || {}, e._sentryDebugIds[t] = "f4adf371-7dd4-48f1-a3ca-3f88d9fc88dc", e._sentryDebugIdIdentifier = "sentry-dbid-f4adf371-7dd4-48f1-a3ca-3f88d9fc88dc");
	} catch {}
})();
import { Button as e, Checkbox as t, DUPLICATES_KEY as n, EmptyState as r, FilterActionButton as i, FilterGlassRows as a, Gg as o, H7 as ee, JZ as s, KEEP_LABELS as c, KEPT_DUPLICATES_KEY as l, LOC as u, M6 as te, MEDIA_SOURCES_KEY as d, MEDIA_SOURCE_ICONS as f, Note as p, SelectAllButton as m, SelectionDock as h, SortKeys as g, SourceLabel as ne, SourceMark as _, TRASH_KEY as v, __toESM as y, batchOperate as b, bulkCloudPreferences as re, busyProps as ie, cardClass as ae, cloudLocations as oe, confirmModal as se, coverUrl as x, duplicateVictims as S, enterPageSelection as C, errorMessage as ce, exitPageSelection as le, fetchDuplicates as ue, fetchKeptDuplicates as de, fetchMediaSources as fe, fmtDur as w, fmtSize as T, formatBitrate as pe, formatFps as E, formatResolution as D, groupKey as O, keepGroup as me, keepGroups as k, middleTruncateCut as A, mixedCloudPreferences as he, queryClient as j, qx as ge, require_jsx_runtime as M, require_react as N, runBulkAction as _e, spriteGlyph as P, t as F, useMutation as ve, usePageSelection as ye, useQuery as I, useQueueSort as be, useWorkContextMenu as xe, victimBytes as L } from "./peach-app.js";
import { ComparisonText as R } from "./peach-app.comparison-text-d2N41j2E.js";
// src/react/components/filename-comparison.tsx
var z = /* @__PURE__ */ y(N(), 1), B = M();
function V({ value: e, reference: t, onOpen: n }) {
	let r = (0, z.useRef)(null), [i, a] = (0, z.useState)(null);
	return (0, z.useLayoutEffect)(() => {
		let t = r.current;
		if (!t) return;
		let n = !0, i = () => {
			if (!n) return;
			let r = A(t, e);
			a((e) => e?.start === r?.start && e?.end === r?.end ? e : r);
		};
		i();
		let o = typeof ResizeObserver > "u" ? null : new ResizeObserver(i);
		return o?.observe(t), t.parentElement && o?.observe(t.parentElement), document.fonts?.ready.then(i), () => {
			n = !1, o?.disconnect();
		};
	}, [e]), /* @__PURE__ */ (0, B.jsx)("button", {
		ref: r,
		type: "button",
		onClick: n,
		title: e,
		"aria-label": e,
		"data-middle-truncate": "",
		"data-middle-truncate-within": "",
		"data-middle-truncate-managed": "",
		onCopy: (t) => {
			t.clipboardData.setData("text/plain", e), t.preventDefault();
		},
		className: "min-w-0 shrink cursor-pointer truncate text-left text-body-regular hover:text-text-secondary",
		children: /* @__PURE__ */ (0, B.jsx)(R, {
			value: e,
			reference: t,
			cut: i
		})
	});
}
// src/react/duplicates/duplicates-page.tsx
var H = P("play"), Se = P("file-stack"), Ce = ae({
	padding: "none",
	radius: "surface",
	className: "mb-6 overflow-hidden dark:bg-background-primary-default"
}), U = "rounded-sm px-1.5 py-px text-caption-1-regular leading-5", W = "rounded-sm px-2 py-0.5 text-caption-1-regular leading-5", G = "font-mono text-caption-1-regular leading-5 text-text-secondary", K = () => {
	j.invalidateQueries({ queryKey: n }), j.invalidateQueries({
		queryKey: v,
		exact: !0
	});
}, q = (e) => e.reduce((e, t) => e + t.files.length, 0);
function J(e, t) {
	let n = [];
	return {
		key: `keep-${e}`,
		label: t,
		reversal: "undo",
		danger: e === "all",
		holdToConfirm: !0,
		confirm: (t) => {
			let n = S(t, e);
			return {
				title: F("cleanup:duplicates.moveToTrash"),
				danger: e === "all",
				body: F("cleanup:duplicates.trashBody", {
					count: n.length,
					groups: t.length,
					keep: c[e] ?? c.largest,
					size: T(L(t, n))
				})
			};
		},
		run: async (t) => (n = S(t, e), await b(n, "dispose"), K(), async () => {
			await b(n, "restore"), K();
		}),
		receipt: () => F("cleanup:duplicates.movedToTrash", { count: n.length })
	};
}
var we = (e) => ({
	key: "keep-all",
	label: e,
	reversal: "undo",
	confirm: (e) => ({
		title: F("cleanup:duplicates.markKeepAll"),
		body: F("cleanup:duplicates.keepAllBody", {
			count: e.length,
			files: q(e)
		}),
		recovery: F("cleanup:duplicates.keepAllRecovery")
	}),
	run: async (e) => (await k(e, !0), K(), async () => {
		await k(e, !1), K();
	}),
	receipt: (e) => F("cleanup:duplicates.keptGroups", { count: e.length })
}), Te = (e) => ({
	key: "unkeep",
	label: e,
	reversal: "undo",
	confirm: (e) => ({
		title: F("cleanup:duplicates.unkeep"),
		body: F("cleanup:duplicates.unkeepBody", { count: e.length })
	}),
	run: async (e) => (await k(e, !1), K(), async () => {
		await k(e, !0), K();
	}),
	receipt: (e) => F("cleanup:duplicates.unkeptGroups", { count: e.length })
});
function Ee(e) {
	return e.identical ? /* @__PURE__ */ (0, B.jsx)("span", {
		className: `${W} text-(--keep)`,
		children: F("cleanup:duplicates.sha1Match")
	}) : /* @__PURE__ */ (0, B.jsx)("span", {
		className: `${W} text-text-secondary`,
		children: e.evidence === "same_code_short_copy" ? F("cleanup:duplicates.sameCodeShorter") : F("cleanup:duplicates.byDuration")
	});
}
function De({ file: e, reference: n, openItem: r, selected: i, onSelect: a, onTrash: s, busy: c }) {
	let l = xe(), d = () => r(e.id), p = [{
		id: "open",
		label: F("catalog:mediaActions.open"),
		icon: o,
		run: d
	}];
	a && p.push({
		id: "select",
		label: F(i ? "catalog:mediaActions.deselect" : "catalog:mediaActions.select"),
		icon: ee,
		run: () => a(!i)
	}), s && p.push({
		id: "trash",
		label: F("cleanup:duplicates.moveToTrash"),
		icon: te,
		danger: !0,
		disabled: c,
		run: s
	});
	let m = {
		key: e.id,
		operations: p
	}, h = u[e.location] || e.location || e.drive, g = `/thumb?id=${e.id}&c=4`;
	return /* @__PURE__ */ (0, B.jsxs)("div", {
		"data-duplicate-file": e.id,
		className: "duplicate-row items-center gap-3 border-t border-separator-border px-5 py-4 max-compact:p-4",
		onContextMenu: (e) => l.onContextMenu(e, m),
		onKeyDown: (e) => l.onKeyDown(e, m),
		children: [
			l.menu,
			/* @__PURE__ */ (0, B.jsxs)("button", {
				type: "button",
				onClick: d,
				"aria-label": F("cleanup:duplicates.previewFile", { name: e.name }),
				className: "relative row-span-3 inline-grid aspect-16/10 w-full cursor-pointer place-items-center overflow-hidden rounded-2lg bg-media-placeholder text-text-secondary",
				children: [/* @__PURE__ */ (0, B.jsx)(H, {
					"aria-hidden": !0,
					className: "size-6"
				}), /* @__PURE__ */ (0, B.jsx)("img", {
					src: e.has_cover ? x(e, 2) : g,
					alt: "",
					loading: "lazy",
					"data-drop": "self",
					"data-fallbacks": e.has_cover ? g : void 0,
					className: "absolute inset-0 size-full object-contain"
				}, e.cover_version || g)]
			}),
			/* @__PURE__ */ (0, B.jsxs)("span", {
				className: "flex min-w-0 items-center gap-2 max-duplicate-narrow:col-start-2 max-duplicate-narrow:-col-end-1",
				children: [
					a ? /* @__PURE__ */ (0, B.jsx)(t, {
						slot: null,
						"aria-label": F("cleanup:duplicates.selectFile", { name: e.name }),
						isSelected: i,
						onChange: a
					}) : null,
					/* @__PURE__ */ (0, B.jsx)(V, {
						value: e.name,
						reference: n?.name,
						onOpen: d
					}),
					e.is_largest || e.is_longest || e.is_highest_bitrate || e.is_new ? /* @__PURE__ */ (0, B.jsxs)("span", {
						className: "flex flex-none gap-1",
						children: [
							e.is_new ? /* @__PURE__ */ (0, B.jsx)("i", {
								className: `${U} not-italic bg-background-primary-hover text-text-primary`,
								children: F("cleanup:duplicates.newCopy")
							}) : null,
							e.is_largest ? /* @__PURE__ */ (0, B.jsx)("i", {
								className: `${U} not-italic bg-background-primary-hover text-text-secondary`,
								children: F("cleanup:duplicates.largest")
							}) : null,
							e.is_longest ? /* @__PURE__ */ (0, B.jsx)("i", {
								className: `${U} not-italic bg-(--keep)/22 text-(--keep)`,
								children: F("cleanup:duplicates.longest")
							}) : null,
							e.is_highest_bitrate ? /* @__PURE__ */ (0, B.jsx)("i", {
								className: `${U} not-italic bg-background-primary-hover text-text-secondary`,
								children: F("cleanup:duplicates.highestBitrate")
							}) : null
						]
					}) : null
				]
			}),
			/* @__PURE__ */ (0, B.jsxs)("span", {
				className: `${G} flex min-w-0 items-center gap-1.5`,
				children: [/* @__PURE__ */ (0, B.jsx)(_, { mark: f[e.location] || "database" }), /* @__PURE__ */ (0, B.jsx)("span", {
					title: h,
					className: "min-w-0 truncate",
					children: h
				})]
			}),
			/* @__PURE__ */ (0, B.jsx)("span", {
				className: G,
				children: T(e.size || 0)
			}),
			/* @__PURE__ */ (0, B.jsx)("span", {
				className: G,
				children: w(e.duration)
			}),
			/* @__PURE__ */ (0, B.jsxs)("span", {
				className: `${G} col-start-2 -col-end-1 flex min-w-0 flex-wrap gap-x-4 gap-y-0.5`,
				children: [
					/* @__PURE__ */ (0, B.jsx)("span", {
						title: F("cleanup:duplicates.resolutionLabel"),
						children: D(e)
					}),
					/* @__PURE__ */ (0, B.jsx)("span", {
						title: F("cleanup:duplicates.bitrateLabel"),
						children: pe(e.bitrate)
					}),
					/* @__PURE__ */ (0, B.jsx)("span", {
						title: F("cleanup:duplicates.fpsLabel"),
						children: E(e.fps)
					})
				]
			}),
			/* @__PURE__ */ (0, B.jsx)("span", {
				className: `${G} col-start-2 -col-end-1 min-w-0 pt-0.5 wrap-anywhere max-duplicate-narrow:col-span-full`,
				children: /* @__PURE__ */ (0, B.jsx)(R, {
					value: e.path ?? "",
					reference: n?.path ?? void 0
				})
			})
		]
	});
}
function Oe({ openItem: o, toast: f, failure: _ }) {
	let v = xe(), [y, ae] = (0, z.useState)("pending"), x = I({
		queryKey: n,
		queryFn: ({ signal: e }) => ue(e)
	}), w = I({
		queryKey: l,
		queryFn: ({ signal: e }) => de(e),
		enabled: y === "kept"
	}), pe = I({
		queryKey: d,
		queryFn: ({ signal: e }) => fe(e)
	}), [E, D] = (0, z.useState)(""), [k, A] = (0, z.useState)(/* @__PURE__ */ new Set()), [j, M] = (0, z.useState)(/* @__PURE__ */ new Set());
	ye(() => {
		A(/* @__PURE__ */ new Set()), M(/* @__PURE__ */ new Set());
	});
	let N = {
		receipt: f,
		failure: (e) => _(F("cleanup:duplicates.bulkFailed"), e)
	}, P = ve({
		mutationFn: (e) => b(e, "dispose"),
		onSuccess: (e, t) => {
			M((e) => new Set([...e].filter((e) => !t.includes(e)))), K(), f(F("cleanup:duplicates.movedToTrash", { count: t.length }), { undo: async () => {
				try {
					await b(t, "restore");
				} catch (e) {
					_(F("cleanup:duplicates.undoTrash"), e);
				} finally {
					K();
				}
			} });
		},
		onSettled: () => D("")
	}), R = ve({
		mutationFn: ({ group: e, on: t }) => me(e.files.map((e) => e.id), t),
		onSuccess: (e, { group: t, on: n }) => {
			K(), f(F(n ? "cleanup:duplicates.keptAll" : "cleanup:duplicates.unkeptOne", { code: t.code }), { undo: async () => {
				try {
					await me(t.files.map((e) => e.id), !n);
				} catch (e) {
					_(F("cleanup:duplicates.undoKeepAll"), e);
				} finally {
					K();
				}
			} });
		},
		onError: (e) => _(F("cleanup:duplicates.markKeepAll"), e),
		onSettled: () => D("")
	}), V = be("duplicates", { size: (e) => Number(e.reclaimable || 0) }), H = y === "kept", U = H ? w.data : x.data, G = H ? w.error : x.error;
	if (!U) return H && w.isPending ? /* @__PURE__ */ (0, B.jsx)("div", { className: "mx-auto w-full max-w-board" }) : /* @__PURE__ */ (0, B.jsx)("div", {
		className: "mx-auto w-full max-w-board",
		children: /* @__PURE__ */ (0, B.jsx)(p, {
			tone: "error",
			title: F("cleanup:duplicates.loadFailed"),
			children: G ? ce(G) : F("cleanup:duplicates.listUnavailable")
		})
	});
	let q = V.sort(U.groups ?? []), Oe = Number(x.data?.kept ?? U.kept ?? 0), Y = oe(pe.data), X = q.filter((e) => k.has(O(e))), ke = (e) => {
		A(/* @__PURE__ */ new Set()), M(/* @__PURE__ */ new Set()), ae(e);
	}, Ae = (e, t) => {
		t && C(), A((n) => {
			let r = new Set(n);
			return t ? r.add(O(e)) : r.delete(O(e)), r;
		});
	}, Z = (e, t) => {
		E || (D(t), _e(e, q, N).catch(N.failure).finally(() => D("")));
	}, Q = ({ groups: e, keep: t, key: n }) => {
		if (P.isPending) return;
		let r = S(e, t);
		r.length && se({
			title: F("cleanup:duplicates.moveToTrash"),
			body: F("cleanup:duplicates.trashBody", {
				count: r.length,
				groups: e.length,
				keep: c[t] ?? c.largest,
				size: T(L(e, r))
			}) + F("shell:bulkAction.canUndo"),
			confirmLabel: F("cleanup:duplicates.moveToTrash"),
			holdToConfirm: !0,
			onConfirm: () => (D(n), P.mutateAsync(r))
		});
	}, je = (e, t) => {
		t && C(), M((n) => {
			let r = new Set(n);
			return t ? r.add(e) : r.delete(e), r;
		});
	}, Me = (e, t, n = j) => {
		if (E) return;
		let r = e.files.filter((e) => n.has(e.id)).map((e) => e.id);
		r.length && se({
			title: F("cleanup:duplicates.moveToTrash"),
			body: F("cleanup:duplicates.selectedTrashBody", {
				count: r.length,
				remaining: e.files.length - r.length,
				size: T(L([e], r))
			}) + F("shell:bulkAction.canUndo"),
			confirmLabel: F("cleanup:duplicates.moveToTrash"),
			holdToConfirm: !0,
			onConfirm: () => (D(t), P.mutateAsync(r))
		});
	}, $ = (e) => ie(E === e && (P.isPending || R.isPending)), Ne = (e, t, n) => {
		R.isPending || P.isPending || (D(t), R.mutate({
			group: e,
			on: n
		}));
	}, Pe = /* @__PURE__ */ (0, B.jsx)(m, {
		label: F("cleanup:duplicates.selectPage"),
		picked: X.length,
		total: q.length,
		onChange: (e) => {
			e && C(), A(e ? new Set(q.map(O)) : /* @__PURE__ */ new Set());
		}
	}), Fe = H ? [Te(F("cleanup:duplicates.unkeep"))] : [
		J("largest", F("cleanup:duplicates.keepLargest")),
		J("longest", F("cleanup:duplicates.keepLongest")),
		...re(X, Y).map((e) => J(e, F("cleanup:duplicates.keepStorage", { storage: u[e] || e }))),
		we(F("cleanup:duplicates.keepAll")),
		J("all", F("cleanup:duplicates.trashGroup"))
	];
	return /* @__PURE__ */ (0, B.jsxs)("div", {
		className: "mx-auto w-full max-w-board pb-10.5",
		children: [
			v.menu,
			/* @__PURE__ */ (0, B.jsx)(a, {
				label: F(H ? "cleanup:duplicates.keptLabel" : "cleanup:duplicates.bulkKeep"),
				topLabel: F(H ? "cleanup:duplicates.keptLabel" : "cleanup:duplicates.bulkKeep"),
				attrs: {
					"data-catalog-frame": "",
					"data-filter-frame": "",
					"data-duplicates-frame": ""
				},
				bottomClassName: "min-h-12",
				top: H ? /* @__PURE__ */ (0, B.jsxs)(B.Fragment, { children: [
					q.length ? /* @__PURE__ */ (0, B.jsx)(i, {
						busy: E === "all:unkeep",
						onPress: () => Z(Te(F("cleanup:duplicates.allUnkeep")), "all:unkeep"),
						children: F("cleanup:duplicates.allUnkeep")
					}) : null,
					/* @__PURE__ */ (0, B.jsx)("span", { className: "ml-auto" }),
					/* @__PURE__ */ (0, B.jsx)(i, {
						onPress: () => ke("pending"),
						children: F("cleanup:duplicates.backToPending")
					})
				] }) : /* @__PURE__ */ (0, B.jsxs)(B.Fragment, { children: [
					q.length ? /* @__PURE__ */ (0, B.jsxs)(B.Fragment, { children: [
						/* @__PURE__ */ (0, B.jsx)(i, {
							busy: E === "all:largest",
							onPress: () => Z(J("largest", ""), "all:largest"),
							children: F("cleanup:duplicates.allKeepLargest")
						}),
						/* @__PURE__ */ (0, B.jsx)(i, {
							busy: E === "all:longest",
							onPress: () => Z(J("longest", ""), "all:longest"),
							children: F("cleanup:duplicates.allKeepLongest")
						}),
						re(q, Y).map((e) => /* @__PURE__ */ (0, B.jsx)(i, {
							busy: E === `all:${e}`,
							onPress: () => Z(J(e, ""), `all:${e}`),
							children: /* @__PURE__ */ (0, B.jsx)(ne, {
								source: e,
								label: F("cleanup:duplicates.allPreferStorage", { storage: u[e] || e })
							})
						}, e)),
						/* @__PURE__ */ (0, B.jsx)(i, {
							busy: E === "all:keep",
							onPress: () => Z(we(""), "all:keep"),
							children: F("cleanup:duplicates.allKeepAll")
						})
					] }) : null,
					/* @__PURE__ */ (0, B.jsx)("span", { className: "ml-auto" }),
					/* @__PURE__ */ (0, B.jsx)(i, {
						onPress: () => ke("kept"),
						children: F("cleanup:duplicates.viewKept", { count: Oe })
					})
				] }),
				bottom: /* @__PURE__ */ (0, B.jsxs)(B.Fragment, { children: [/* @__PURE__ */ (0, B.jsxs)("span", {
					"data-catalog-summary": "",
					children: [/* @__PURE__ */ (0, B.jsxs)("span", {
						"data-catalog-readout": "",
						role: "status",
						children: [
							F(H ? "cleanup:duplicates.keptLabel" : "cleanup:duplicates.summaryLabel"),
							" · ",
							F("cleanup:duplicates.groupCount", { count: Number(U.total || 0) }),
							" · ",
							H ? F("cleanup:duplicates.keptDetail", { count: Number(U.files || 0) }) : F("cleanup:duplicates.summaryDetail", {
								count: Number(U.files || 0),
								size: T(U.reclaimable)
							})
						]
					}), q.length ? Pe : null]
				}), /* @__PURE__ */ (0, B.jsx)("span", {
					"data-entity-sorts": "",
					children: /* @__PURE__ */ (0, B.jsx)(g, {
						sorts: V.sorts,
						onSort: V.onSort
					})
				})] })
			}),
			/* @__PURE__ */ (0, B.jsx)(h, {
				label: F("cleanup:duplicates.dockLabel"),
				visible: X.length > 0,
				count: F("cleanup:duplicates.selectedGroups", { count: X.length }),
				actions: Fe.map((e) => ({
					action: e,
					items: X,
					host: N,
					done: () => A(/* @__PURE__ */ new Set())
				})),
				children: /* @__PURE__ */ (0, B.jsx)(e, {
					variant: "ghost",
					size: "small",
					onClick: le,
					children: F("cleanup:duplicates.clearSelection")
				})
			}),
			P.isError ? /* @__PURE__ */ (0, B.jsx)("div", {
				className: "mb-5",
				children: /* @__PURE__ */ (0, B.jsx)(p, {
					tone: "error",
					title: F("cleanup:duplicates.trashFailed"),
					children: ce(P.error)
				})
			}) : null,
			q.length ? q.map((n, r) => {
				let i = [n], a = (e) => `${r}:${e}`, c = k.has(O(n)), l = () => {
					let e = [{
						id: "select",
						label: c ? F("catalog:mediaActions.deselect") : F("cleanup:duplicates.selectGroup", { code: n.code }),
						icon: ee,
						run: () => Ae(n, !c)
					}, {
						id: "keep",
						label: F(H ? "cleanup:duplicates.unkeep" : "cleanup:duplicates.keepAll"),
						icon: H ? s : ge,
						disabled: !!E,
						run: () => Ne(n, a("keep"), !H)
					}];
					if (!H) {
						let t = [
							["largest", F("cleanup:duplicates.keepLargest")],
							["longest", F("cleanup:duplicates.keepLongest")],
							...he(n.files, Y).map((e) => [e, F("cleanup:duplicates.keepStorage", { storage: u[e] || e })]),
							["all", F("cleanup:duplicates.trashGroup")]
						];
						for (let [n, r] of t) e.push({
							id: n,
							label: r,
							icon: n === "all" ? te : ge,
							danger: n === "all",
							disabled: !!E,
							run: () => Q({
								groups: i,
								keep: n,
								key: a(n)
							})
						});
					}
					return {
						key: O(n),
						operations: e
					};
				};
				return /* @__PURE__ */ (0, B.jsxs)("section", {
					"aria-label": n.code,
					className: Ce,
					"data-board-selected": k.has(O(n)) || void 0,
					children: [/* @__PURE__ */ (0, B.jsxs)("div", {
						"data-duplicate-group-tools": "",
						className: "flex flex-wrap items-center gap-3 bg-background-tertiary-default p-5 max-compact:p-4 dark:bg-background-secondary-default",
						onContextMenu: (e) => v.onContextMenu(e, l()),
						onKeyDown: (e) => {
							(e.key === "ContextMenu" || e.shiftKey && e.key === "F10") && v.onKeyDown(e, l());
						},
						children: [
							/* @__PURE__ */ (0, B.jsx)(t, {
								slot: null,
								"aria-label": F("cleanup:duplicates.selectGroup", { code: n.code }),
								isSelected: k.has(O(n)),
								onChange: (e) => Ae(n, e)
							}),
							/* @__PURE__ */ (0, B.jsx)("b", {
								className: "text-title-2-medium text-text-primary",
								children: n.code
							}),
							/* @__PURE__ */ (0, B.jsx)("span", {
								className: "font-mono text-caption-1-regular leading-5 text-text-primary",
								children: F("cleanup:duplicates.groupDetail", {
									count: Number(n.count || 0),
									size: T(n.reclaimable)
								})
							}),
							Ee(n),
							n.new_files ? /* @__PURE__ */ (0, B.jsx)("span", {
								className: `${W} text-text-primary`,
								children: F("cleanup:duplicates.newFiles", { count: n.new_files })
							}) : null,
							n.cross_drive ? /* @__PURE__ */ (0, B.jsx)("span", {
								className: `${W} text-text-secondary`,
								children: F("cleanup:duplicates.crossDrive", { drives: n.drives.join(" ") })
							}) : null,
							/* @__PURE__ */ (0, B.jsx)("span", {
								className: "ml-auto flex flex-wrap gap-2 max-compact:ml-0 max-compact:w-full",
								children: H ? /* @__PURE__ */ (0, B.jsx)(e, {
									variant: "secondary",
									size: "small",
									...$(a("unkeep")),
									onClick: () => Ne(n, a("unkeep"), !1),
									children: F("cleanup:duplicates.unkeep")
								}) : /* @__PURE__ */ (0, B.jsxs)(B.Fragment, { children: [
									/* @__PURE__ */ (0, B.jsx)(e, {
										variant: "danger",
										size: "small",
										...$(a("files")),
										disabled: E !== "" || !n.files.some((e) => j.has(e.id)),
										onClick: () => Me(n, a("files")),
										children: F("cleanup:duplicates.trashSelectedFiles", { count: n.files.filter((e) => j.has(e.id)).length })
									}),
									/* @__PURE__ */ (0, B.jsx)(e, {
										variant: "secondary",
										size: "small",
										...$(a("largest")),
										onClick: () => Q({
											groups: i,
											keep: "largest",
											key: a("largest")
										}),
										children: F("cleanup:duplicates.keepLargest")
									}),
									/* @__PURE__ */ (0, B.jsx)(e, {
										variant: "secondary",
										size: "small",
										...$(a("longest")),
										onClick: () => Q({
											groups: i,
											keep: "longest",
											key: a("longest")
										}),
										children: F("cleanup:duplicates.keepLongest")
									}),
									he(n.files, Y).map((t) => /* @__PURE__ */ (0, B.jsx)(e, {
										variant: "secondary",
										size: "small",
										...$(a(t)),
										onClick: () => Q({
											groups: i,
											keep: t,
											key: a(t)
										}),
										children: /* @__PURE__ */ (0, B.jsx)(ne, {
											source: t,
											label: F("cleanup:duplicates.keepStorage", { storage: u[t] || t })
										})
									}, t)),
									/* @__PURE__ */ (0, B.jsx)(e, {
										variant: "secondary",
										size: "small",
										...$(a("keep")),
										onClick: () => Ne(n, a("keep"), !0),
										children: F("cleanup:duplicates.keepAll")
									}),
									/* @__PURE__ */ (0, B.jsx)(e, {
										variant: "danger",
										size: "small",
										...$(a("all")),
										onClick: () => Q({
											groups: i,
											keep: "all",
											key: a("all")
										}),
										children: F("cleanup:duplicates.trashGroup")
									})
								] })
							})
						]
					}), /* @__PURE__ */ (0, B.jsx)("div", { children: n.files.map((e) => /* @__PURE__ */ (0, B.jsx)(De, {
						file: e,
						reference: n.files.find((t) => t.id !== e.id),
						openItem: o,
						selected: j.has(e.id),
						onSelect: H ? void 0 : (t) => je(e.id, t),
						busy: !!E,
						onTrash: H ? void 0 : () => Me(n, a("files"), /* @__PURE__ */ new Set([e.id]))
					}, e.id)) })]
				}, O(n));
			}) : H ? /* @__PURE__ */ (0, B.jsx)(r, {
				icon: Se,
				title: F("cleanup:duplicates.keptEmptyTitle"),
				children: F("cleanup:duplicates.keptEmptyBody")
			}) : /* @__PURE__ */ (0, B.jsx)(r, {
				icon: Se,
				title: F("cleanup:duplicates.emptyTitle"),
				children: F("cleanup:duplicates.emptyBody")
			}),
			q.length > 0 && U.total > q.length ? /* @__PURE__ */ (0, B.jsx)("p", {
				className: "text-center text-caption-1-regular text-text-secondary",
				children: F("cleanup:duplicates.topGroups", {
					shown: q.length.toLocaleString(),
					count: Number(U.total)
				})
			}) : null
		]
	});
}
export { Oe as DuplicatesPage };

//# debugId=f4adf371-7dd4-48f1-a3ca-3f88d9fc88dc