<script lang="ts">
	import { createEventDispatcher, onMount } from "svelte";
	import { csvParse } from "d3-dsv";
	import { scaleLinear } from "d3-scale";
	import { line as _line, curveLinear } from "d3-shape";

	import { colors as color_palette, ordered_colors } from "@gradio/theme";
	import { get_next_color } from "@gradio/utils";

	import { get_domains, transform_values } from "./utils";

	import { tooltip } from "@gradio/tooltip";

	export let value: string | Record<string, string>[];
	export let x: string | undefined = undefined;
	export let y: string[] | undefined = undefined;
	export let colors: string[] = [];

	const dispatch = createEventDispatcher();

	$: ({ x: _x, y: _y } =
		typeof value === "string"
			? transform_values(csvParse(value) as Record<string, string>[], x, y)
			: transform_values(value, x, y));

	$: x_domain = get_domains(_x);
	$: y_domain = get_domains(_y);

	$: scale_x = scaleLinear(x_domain, [0, 600]).nice();
	$: scale_y = scaleLinear(y_domain, [350, 0]).nice();
	$: x_ticks = scale_x.ticks(8);
	$: y_ticks = scale_y.ticks(8);

	let color_map: Record<string, string>;
	$: color_map = _y.reduce(
		(acc, next, i) => ({ ...acc, [next.name]: get_color(i) }),
		{}
	);

	function get_color(index: number): string {
		let current_color = colors[index % colors.length];

		if (current_color && current_color in color_palette) {
			return color_palette[current_color as keyof typeof color_palette]
				?.primary;
		} else if (!current_color) {
			return color_palette[get_next_color(index) as keyof typeof color_palette]
				.primary;
		}
		return current_color;
	}

	onMount(() => {
		dispatch("process", { x: _x, y: _y });
	});
</script>

<div class="wrap">
	<div class="legend">
		{#each _y as { name }}
			<div class="legend-item">
				<span class="legend-box" style="background-color: {color_map[name]}" />
				{name}
			</div>
		{/each}
	</div>
	<svg class="w-full" viewBox="-70 -20 700 420">
		<g>
			{#each x_ticks as tick}
				<line
					stroke-width="0.5"
					x1={scale_x(tick)}
					x2={scale_x(tick)}
					y1={scale_y(y_ticks[0] < y_domain[0] ? y_ticks[0] : y_domain[0]) + 10}
					y2={scale_y(
						y_domain[1] > y_ticks[y_ticks.length - 1]
							? y_domain[1]
							: y_ticks[y_ticks.length - 1]
					)}
					stroke="#aaa"
				/>
				<text
					class="label-text"
					text-anchor="middle"
					x={scale_x(tick)}
					y={scale_y(y_ticks[0]) + 30}
				>
					{tick}
				</text>
			{/each}

			{#each y_ticks as tick}
				<line
					stroke-width="0.5"
					y1={scale_y(tick)}
					y2={scale_y(tick)}
					x1={scale_x(x_ticks[0] < x_domain[0] ? x_ticks[0] : x_domain[0]) - 10}
					x2={scale_x(
						x_domain[1] > x_ticks[x_ticks.length - 1]
							? x_domain[1]
							: x_ticks[x_ticks.length - 1]
					)}
					stroke="#aaa"
				/>

				<text
					class="label-text"
					text-anchor="end"
					y={scale_y(tick) + 4}
					x={scale_x(x_ticks[0]) - 20}
				>
					{tick}
				</text>
			{/each}

			{#if y_domain[1] > y_ticks[y_ticks.length - 1]}
				<line
					stroke-width="0.5"
					y1={scale_y(y_domain[1])}
					y2={scale_y(y_domain[1])}
					x1={scale_x(x_ticks[0])}
					x2={scale_x(x_domain[1])}
					stroke="#aaa"
				/>
				<text
					class="label-text"
					text-anchor="end"
					y={scale_y(y_domain[1]) + 4}
					x={scale_x(x_ticks[0]) - 20}
				>
					{y_domain[1]}
				</text>
			{/if}
		</g>

		{#each _y as { name, values }}
			{@const color = color_map[name]}
			{#each values as { x, y }}
				<circle
					r="3.5"
					cx={scale_x(x)}
					cy={scale_y(y)}
					stroke-width="1.5"
					stroke={color}
					fill="none"
				/>
			{/each}
			<path
				d={_line().curve(curveLinear)(
					values.map(({ x, y }) => [scale_x(x), scale_y(y)])
				)}
				fill="none"
				stroke={color}
				stroke-width="3"
			/>
		{/each}

		{#each _y as { name, values }}
			{@const color = color_map[name]}
			{#each values as { x, y }}
				<circle
					use:tooltip={{ color, text: `(${x}, ${y})` }}
					r="7"
					cx={scale_x(x)}
					cy={scale_y(y)}
					stroke="black"
					fill="black"
					style="cursor: pointer; opacity: 0"
				/>
			{/each}
		{/each}
	</svg>

	<div class="main-label">
		{_x.name}
	</div>
</div>

<style>
	.wrap {
		margin-top: var(--size-3);
	}

	.legend {
		display: flex;
		justify-content: center;
		align-items: center;
		color: var(--body-text-color);
	}

	.legend-item {
		display: flex;
		align-items: center;
		gap: var(--spacing-sm);
		margin-right: var(--size-2);
		margin-left: var(--size-2);
	}

	.legend-box {
		display: inline-block;
		border-radius: var(--radius-xs);
		width: var(--size-3);
		height: var(--size-3);
	}

	svg {
		width: var(--size-full);
	}

	.label-text {
		fill: var(--body-text-color);
		font-size: var(--text-sm);
		font-family: var(--font-mono);
	}

	.main-label {
		display: flex;
		justify-content: center;
		align-items: center;
		color: var(--body-text-color);
	}
</style>
