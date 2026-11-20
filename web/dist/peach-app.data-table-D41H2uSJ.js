(function() {
	try {
		var e = typeof globalThis < "u" ? globalThis : typeof window < "u" ? window : typeof global < "u" ? global : typeof self < "u" ? self : {}, t = new e.Error().stack;
		t && (e._sentryDebugIds = e._sentryDebugIds || {}, e._sentryDebugIds[t] = "36df0ac3-3356-4446-a2c9-6328ee3ac3e9", e._sentryDebugIdIdentifier = "sentry-dbid-36df0ac3-3356-4446-a2c9-6328ee3ac3e9");
	} catch {}
})();
import { $76d00c5a4edb230a$export$76ccd210b9029917 as e, $76d00c5a4edb230a$export$816b5d811295e6bc as t, $76d00c5a4edb230a$export$b59bdbef9ce70de2 as n, $76d00c5a4edb230a$export$f6f0c3fe4ec306ea as r, $76d00c5a4edb230a$export$f850895b287ef28e as i, ActivityStatus as a, Button as ee, Checkbox as te, ChevronSortDown as o, DataTableFooter as s, DataTableFrame as ne, DataTableSort as c, SelectionDock as l, Table as u, TableColumnControls as d, TableColumnResizer as re, TableSelectionHeader as ie, __toESM as f, cardClass as ae, collationLocale as p, columnVisibilityFeature as m, createColumnHelper as oe, enterPageSelection as se, exitPageSelection as ce, flexRender as h, require_jsx_runtime as g, require_react as _, rowPaginationFeature as v, rowSelectionFeature as y, rowSelectionOperation as le, rowSortingFeature as b, runBulkAction as x, t as S, tableFeatures as C, usePageSelection as w, useRowWorkContext as T, useTable as E, useTableFilters as ue, useTablePreferences as de } from "./peach-app.js";
import { createPaginatedRowModel as D, createSortedRowModel as O, useTableSelection as fe } from "./peach-app.use-table-selection-CnuGRvGn.js";
// src/react/components/data-table.tsx
var k = /* @__PURE__ */ f(_(), 1), A = g(), j = C({
	rowSortingFeature: b,
	rowSelectionFeature: y,
	rowPaginationFeature: v,
	columnVisibilityFeature: m,
	sortedRowModel: O(),
	paginatedRowModel: D()
});
function M({ label: f, items: m, columns: g, rowId: _, rowLabel: v, selected: y, onSelected: b, actions: C, controls: D, title: O = f, titleId: M, description: N, footerActions: P, toolbarActions: F, panel: I = !0, unit: L = S("shell:dataTable.recordUnit"), filters: R, busy: z, contextOperations: B }) {
	let [V, H] = (0, k.useState)([]), pe = (0, k.useMemo)(() => [{
		id: "select",
		label: S("shell:dataTable.selectColumn"),
		width: 48,
		min: 48,
		max: 48,
		required: !0
	}, ...g.map((e, t) => ({
		...e,
		width: e.width ?? (t === 0 ? 320 : 160),
		min: e.min ?? (t === 0 ? 320 : 96),
		flex: e.flex ?? t === 0,
		required: t === 0
	}))], [g]), U = de(`data:${f}`, pe), [W, G] = (0, k.useState)({
		pageIndex: 0,
		pageSize: 20
	}), K = ue(m, Object.fromEntries(g.filter((e) => e.filter).map((e) => [e.id, e.filter])), () => G((e) => ({
		...e,
		pageIndex: 0
	})), R), [q, me] = (0, k.useState)([]), J = new Map((R ? [...q, ...m] : m).map((e) => [_(e), e])), he = fe(() => b([]));
	w(() => b([])), (0, k.useEffect)(() => {
		y.length && se();
	}, [y.length]);
	let ge = Math.max(1, Math.ceil(K.items.length / W.pageSize)), Y = Math.min(W.pageIndex, ge - 1), X = Object.fromEntries(y.map((e) => [e, !0])), _e = (0, k.useMemo)(() => {
		let e = oe();
		return e.columns([e.display({
			id: "select",
			header: ({ table: e }) => /* @__PURE__ */ (0, A.jsx)(ie, {
				table: e,
				label: S("shell:dataTable.selectAll", { label: f }),
				disabled: z
			}),
			cell: ({ row: e }) => /* @__PURE__ */ (0, A.jsx)(te, {
				slot: null,
				"aria-label": S("shell:dataTable.selectRow", { name: v(e.original) }),
				isSelected: e.getIsSelected(),
				onChange: (t) => e.toggleSelected(t)
			})
		}), ...g.map((t) => e.accessor((e) => t.value?.(e) ?? "", {
			id: t.id,
			header: t.label,
			enableSorting: !!t.value,
			sortFn: (e, n) => {
				let r = t.value(e.original), i = t.value(n.original);
				return typeof r == "number" && typeof i == "number" ? r - i : String(r).localeCompare(String(i), p, { numeric: !0 });
			},
			cell: ({ row: e }) => t.render(e.original)
		}))]);
	}, [
		g,
		f,
		v,
		z
	]), Z = E({
		features: j,
		data: K.items,
		columns: _e,
		getRowId: _,
		state: {
			sorting: V,
			rowSelection: X,
			pagination: {
				...W,
				pageIndex: Y
			},
			columnVisibility: U.visibility
		},
		onColumnVisibilityChange: U.change,
		onSortingChange: (e) => {
			H(e), G((e) => ({
				...e,
				pageIndex: 0
			}));
		},
		onPaginationChange: G,
		enableRowSelection: !0,
		onRowSelectionChange: (e) => {
			let t = typeof e == "function" ? e(X) : e;
			Object.values(t).some(Boolean) && he(), b([...J.values()].filter((e) => t[_(e)]).map(_));
		}
	}), Q = T((e) => J.get(e), z ? void 0 : (e) => {
		let t = _(e), n = C([e], () => Z.setRowSelection(({ [t]: e, ...n }) => n)).flatMap(({ rowAction: e, action: t, host: n, items: r, disabled: i, done: a }) => e && r.length ? [{
			...e,
			id: t.key,
			danger: t.danger,
			disabled: i,
			run: async () => {
				await x(t, r, n) && a?.();
			}
		}] : []);
		return [
			...B?.(e) ?? [],
			le(!!X[t], () => Z.getRow(t)?.toggleSelected()),
			...n
		];
	}), $ = y.flatMap((e) => {
		let t = J.get(e);
		return t ? [t] : [];
	});
	return (0, k.useEffect)(() => {
		(q.length !== $.length || q.some((e, t) => e !== $[t])) && me($);
	}, [$, q]), /* @__PURE__ */ (0, A.jsxs)("div", {
		"data-data-table-panel": I || void 0,
		"aria-busy": z || void 0,
		className: I ? ae({
			padding: "none",
			className: "flex flex-col gap-4 px-6 py-5 max-sm:px-4"
		}) : "flex min-w-0 flex-col gap-4",
		onKeyDown: Q.onKeyDown,
		children: [
			Q.menu,
			/* @__PURE__ */ (0, A.jsxs)("div", {
				"data-responsive-toolbar": "",
				role: "toolbar",
				"aria-label": S("shell:dataTable.toolbar", { label: f }),
				children: [/* @__PURE__ */ (0, A.jsxs)("div", {
					"data-toolbar-heading": "",
					children: [/* @__PURE__ */ (0, A.jsx)("h3", {
						id: M,
						className: "text-title-2-medium text-text-primary",
						children: O
					}), /* @__PURE__ */ (0, A.jsx)("span", {
						className: "text-body-2-regular tabular-nums text-text-secondary",
						children: `${K.items.length.toLocaleString()} ${L}`
					})]
				}), /* @__PURE__ */ (0, A.jsxs)("div", {
					"data-toolbar-actions": "",
					children: [
						F,
						/* @__PURE__ */ (0, A.jsx)(d, {
							preferences: U,
							label: f
						}),
						/* @__PURE__ */ (0, A.jsx)(c, {
							label: f,
							options: g.filter((e) => e.value).map((e) => ({
								id: e.id,
								label: e.label
							})),
							sorting: V,
							onChange: (e) => {
								H(e), G((e) => ({
									...e,
									pageIndex: 0
								}));
							}
						})
					]
				})]
			}),
			N ? /* @__PURE__ */ (0, A.jsx)("p", {
				className: "text-body-2-regular text-text-secondary",
				children: N
			}) : null,
			/* @__PURE__ */ (0, A.jsxs)(l, {
				label: S("shell:dataTable.bulkActions", { label: f }),
				visible: $.length > 0,
				count: S("shell:dataTable.selectedCount", {
					count: $.length,
					unit: L
				}),
				actions: C($, () => b([])),
				children: [D?.($, () => b([])), /* @__PURE__ */ (0, A.jsx)(ee, {
					variant: "ghost",
					size: "small",
					onClick: () => {
						b([]), ce();
					},
					children: S("shell:dataTable.clearSelection")
				})]
			}),
			/* @__PURE__ */ (0, A.jsx)(ne, {
				follow: !0,
				preferences: U,
				onRowClick: (e) => Z.getRow(e)?.toggleSelected(),
				children: /* @__PURE__ */ (0, A.jsxs)(u, {
					"aria-label": f,
					size: "sm",
					sortDescriptor: V[0] ? {
						column: V[0].id,
						direction: V[0].desc ? "descending" : "ascending"
					} : void 0,
					onSortChange: (e) => Z.getColumn(String(e.column))?.toggleSorting(e.direction === "descending"),
					children: [/* @__PURE__ */ (0, A.jsxs)(i, { children: [Z.getHeaderGroups()[0].headers.map((e) => /* @__PURE__ */ (0, A.jsx)(t, {
						id: e.id,
						isRowHeader: e.id === g[0].id,
						allowsSorting: e.column.getCanSort(),
						...U.columnProps(e.id),
						children: ({ sortDirection: t }) => /* @__PURE__ */ (0, A.jsxs)(A.Fragment, { children: [/* @__PURE__ */ (0, A.jsxs)("span", {
							className: "flex items-center gap-0.5",
							children: [K.header(e.id, String(e.column.columnDef.header)) ?? h(e.column.columnDef.header, e.getContext()), e.column.getCanSort() ? /* @__PURE__ */ (0, A.jsx)("span", {
								"data-sort-indicator": !0,
								"data-direction": t || void 0,
								children: /* @__PURE__ */ (0, A.jsx)(o, {})
							}) : null]
						}), /* @__PURE__ */ (0, A.jsx)(re, {
							preferences: U,
							id: e.id
						})] })
					}, e.id)), /* @__PURE__ */ (0, A.jsx)(t, {
						id: "remaining-space",
						"aria-label": S("shell:dataTable.spacerColumn"),
						"data-table-space": "",
						width: U.spaceWidth,
						minWidth: 0
					})] }), /* @__PURE__ */ (0, A.jsx)(e, {
						renderEmptyState: () => z ? null : S("shell:dataTable.empty"),
						children: (z ? [] : Z.getRowModel().rows).map((e) => /* @__PURE__ */ (0, A.jsxs)(n, {
							id: e.id,
							"data-board-selected": e.getIsSelected() || void 0,
							"data-work-context-row": e.id,
							onContextMenu: Q.onContextMenu ? (t) => Q.onContextMenu?.(t, e.original, e.id) : void 0,
							children: [e.getVisibleCells().map((e) => /* @__PURE__ */ (0, A.jsx)(r, { children: h(e.column.columnDef.cell, e.getContext()) }, e.id)), /* @__PURE__ */ (0, A.jsx)(r, { "data-table-space": "" })]
						}, e.id))
					})]
				})
			}),
			z ? /* @__PURE__ */ (0, A.jsx)(a, {
				kind: "linear-dots",
				label: S("shell:spinner.loading")
			}) : null,
			/* @__PURE__ */ (0, A.jsx)(s, {
				label: f,
				total: K.items.length,
				pagination: {
					...W,
					pageIndex: Y
				},
				onChange: G,
				unit: L
			}),
			P ? /* @__PURE__ */ (0, A.jsx)("div", {
				className: "flex flex-wrap items-center justify-end gap-2 border-t border-separator-border pt-4",
				children: P
			}) : null
		]
	});
}
export { M as DataTable };

//# debugId=36df0ac3-3356-4446-a2c9-6328ee3ac3e9