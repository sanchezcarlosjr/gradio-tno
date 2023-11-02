<script lang="ts">
	import {BlockTitle} from "@gradio/atoms";
	import {combination, deepCopy, div, index, mul} from "./helpers";
	import {onMount} from 'svelte';
	import { createEventDispatcher } from "svelte";
	import undoWhite from './undo-white.png';
	import undoBlack from './undo-black.png';
	import reloadWhite from './reload-white.png';
	import reloadBlack from './reload-black.png';


	export let value = {};
	export let value_is_output = false;
	export let lines = 1;
	export let placeholder = "Type here...";
	export let label: string;
	export let info: string | undefined = undefined;
	export let disabled = false;
	export let show_label = true;
	export let container = true;
	export let max_lines: number;
	export let type: "text" | "password" | "email" = "text";
	export let show_copy_button = false;
	export let rtl = false;
	export let autofocus = false;
	export let text_align: "left" | "right" | undefined = undefined;
	export let autoscroll = true;

	const bezier_curve = (T: any, pivots: any) => {
		const n = pivots.length - 1;
		const curve = [];
		for (let t = 0; t <= 1; t += 1 / T) {
			let x = 0;
			let y = 0;
			pivots.forEach((pivot: any, idx: number) => {
				x +=
					combination(idx, n) *
					Math.pow(t, idx) *
					Math.pow(1 - t, n - idx) *
					pivot.x;
				y +=
					combination(idx, n) *
					Math.pow(t, idx) *
					Math.pow(1 - t, n - idx) *
					pivot.y;
			});
			curve.push({x, y});
		}
		return curve;
	};

	const kochanek_bartels_segment = (
		t: any,
		tension: any,
		continuity: any,
		bias: any,
		p0: any,
		p1: any,
		p2: any,
		p3: any
	) => {
		return bezier_curve(t, [
			p1,
			{
				x:
					p1.x +
					((1 - tension) * (1 + bias) * (1 + continuity) * (p1.x - p0.x) +
						(1 - tension) * (1 - bias) * (1 - continuity) * (p2.x - p1.x)) /
					6,
				y:
					p1.y +
					((1 - tension) * (1 + bias) * (1 + continuity) * (p1.y - p0.y) +
						(1 - tension) * (1 - bias) * (1 - continuity) * (p2.y - p1.y)) /
					6,
			},
			{
				x:
					p2.x -
					((1 - tension) * (1 + bias) * (1 - continuity) * (p2.x - p1.x) +
						(1 - tension) * (1 - bias) * (1 + continuity) * (p3.x - p2.x)) /
					6,
				y:
					p2.y -
					((1 - tension) * (1 + bias) * (1 - continuity) * (p2.y - p1.y) +
						(1 - tension) * (1 - bias) * (1 + continuity) * (p3.y - p2.y)) /
					6,
			},
			p2,
		]);
	};

	const kochanek_bartels_curve = (
		t: any,
		vertices: any,
		tension = 0,
		continuity = 0,
		bias = 0
	) => {
		const segments = [];
		const curve = [];
		for (let i = 0; i < vertices.length; ++i) {
			const segment = kochanek_bartels_segment(
				t,
				tension,
				continuity,
				bias,
				vertices[index(vertices, i - 1)],
				vertices[index(vertices, i)],
				vertices[index(vertices, i + 1)],
				vertices[index(vertices, i + 2)]
			);
			segments.push(segment);
			curve.push(...segment);
		}
		return {segments, curve};
	};


	const config = {
		host: 'localhost',
		port: 5000,

		maxStatesCount: 30,
		baseCanvasWidth: 600,
		backgroundColor: '#19212c',
		guideColor: '#094f5e',
		curveColor: '#32c5e3',
		vertexColor: '#a11881',
		focusedVertexColor: '#d9c530',
		vertexRadius: 3,
		focusFactor: 2,
		cursorColor: '#ffffff',
		cursorSize: 10,

		guideLines: 10,
		guideAngle: -20,
		initialVertices: 7,
		baseRadius: 150,
		bezierT: 20,
	};


	let canvas: HTMLCanvasElement;
	const buffer = document.createElement('canvas');
	const states: any[] = [];
	let currentState = -1;
	let vertices: any[] = [];
	let curve: any[] = [];
	let segments: any[] = [];
	let selectedVertex: any;

	const UpdateType = {
		MousePressed: 0,
		MouseReleased: 1,
		MouseMove: 2,
		MouseOut: 3,
		Resize: 4,
		Reset: 5,
		StateChange: 6,
	};

	const MouseButton = {
		Left: 0,
		Middle: 1,
		Right: 2,
	};

	const dispatch = createEventDispatcher<{
		change: string;
		submit: undefined;
	}>();

	const resize = () => {
		// @ts-ignore
		const size = window.getComputedStyle(canvas, '').width.match(/^(\d+)/g)[0];
		// @ts-ignore
		canvas.width = canvas.height = buffer.width = buffer.height = size;
		update(UpdateType.Resize);
	};

	const update = (type: any, mx = 0, my = 0) => {
		const ctx: any = buffer.getContext('2d');
		const t = buffer.width / 2;
		clear(ctx);
		ctx.save();
		ctx.translate(t, t);
		drawCurve(ctx);
		drawVertices(type, ctx, mx - t, my - t);
		ctx.restore();
		drawCursor(ctx, mx, my);
		display();
	};

	const clear = (ctx: CanvasRenderingContext2D) => {
		ctx.fillStyle = config.backgroundColor;
		ctx.fillRect(0, 0, buffer.width, buffer.height);
	};

	const display = () => {
		const ctx: CanvasRenderingContext2D = canvas.getContext('2d') as CanvasRenderingContext2D;
		ctx.drawImage(buffer, 0, 0);
	};

	const drawCursor = (ctx: CanvasRenderingContext2D, mx = 0, my = 0) => {
		if (mx != null && my != null) {
			const w = config.cursorSize / 2;
			ctx.strokeStyle = config.cursorColor;
			drawLine(ctx, {x: mx - w, y: my}, {x: mx + w, y: my});
			drawLine(ctx, {x: mx, y: my - w}, {x: mx, y: my + w});
		}
	};

	const onMouseDown = ({offsetX: mx, offsetY: my, button}: MouseEvent) => {
		const s = buffer.width / config.baseCanvasWidth;
		const t = buffer.width / 2;
		let focusedVertex = getFocusedVertex(mx - t, my - t);
		if (button === MouseButton.Left) {
			selectedVertex = focusedVertex;
			if (!selectedVertex) {
				const focusedSegmentVertex = getFocusedSegmentVertex(mx - t, my - t);
				if (focusedSegmentVertex) {
					selectedVertex = {
						index: focusedSegmentVertex.segment + 1,
						distance: 0,
					};
					vertices.splice(
						selectedVertex.index,
						0,
						div({x: mx - t, y: my - t}, s)
					);
				}
			}
		} else if (
			button === MouseButton.Right &&
			focusedVertex &&
			vertices.length > 4
		) {
			vertices.splice(focusedVertex.index, 1);
			pushState();
		}
		updateCurve();
		update(UpdateType.MousePressed, mx, my);
	};

	const onMouseMoved = ({offsetX: mx, offsetY: my, button}: MouseEvent) => {
		if (button === MouseButton.Left && selectedVertex) {
			const t = buffer.width / 2;
			const s = buffer.width / config.baseCanvasWidth;
			vertices[selectedVertex.index] = div({x: mx - t, y: my - t}, s);
			updateCurve();
		}
		update(UpdateType.MouseMove, mx, my);
	};

	const drawCurve = (ctx: CanvasRenderingContext2D) => {
		const s = buffer.width / config.baseCanvasWidth;
		ctx.strokeStyle = config.guideColor;
		drawCircle(ctx, {x: 0, y: 0}, config.baseRadius * s, 'stroke');
		ctx.save();
		ctx.rotate(config.guideAngle);
		for (let i = 1; i < config.guideLines; ++i) {
			const x =
				config.baseRadius - ((config.baseRadius * 2) / config.guideLines) * i;
			const y = Math.sin(Math.acos(x / config.baseRadius)) * config.baseRadius;
			drawLine(ctx, {x: x * s, y: -y * s}, {x: x * s, y: y * s});
		}
		ctx.restore();
		ctx.strokeStyle = config.curveColor;
		curve.forEach((vertex, idx) => {
			drawLine(ctx, mul(curve[index(curve, idx - 1)], s), mul(vertex, s));
		});
	};

	const drawVertices = (updateType: any, ctx: CanvasRenderingContext2D, mx = 0, my = 0) => {
		let focus = selectedVertex;
		const s = buffer.width / config.baseCanvasWidth;
		ctx.fillStyle = config.vertexColor;
		vertices.forEach((vertex, idx) => {
			vertex = mul(vertex, s);
			drawCircle(ctx, vertex, config.vertexRadius);
			if (!selectedVertex && mx != null && my != null) {
				const distance = Math.sqrt(
					Math.pow(mx - vertex.x, 2) + Math.pow(my - vertex.y, 2)
				);
				if (
					distance <= config.vertexRadius * config.focusFactor &&
					(!focus || distance < focus.distance)
				) {
					focus = {index: idx, distance};
				}
			}
		});
		if (focus) {
			const vertex = vertices[focus.index];
			ctx.strokeStyle = config.focusedVertexColor;
			drawCircle(
				ctx,
				mul(vertex, s),
				config.vertexRadius * config.focusFactor,
				'stroke'
			);
		}
	};

	const drawCircle = (ctx: CanvasRenderingContext2D, {x, y}: any, radius: any, mode = 'fill') => {
		ctx.beginPath();
		ctx.arc(x, y, radius, 0, 2 * Math.PI);
		['fill', 'both'].includes(mode) && ctx.fill();
		['stroke', 'both'].includes(mode) && ctx.stroke();
		ctx.closePath();
	};

	const drawLine = (ctx: CanvasRenderingContext2D, v1: any, v2: any) => {
		ctx.beginPath();
		ctx.moveTo(v1.x, v1.y);
		ctx.lineTo(v2.x, v2.y);
		ctx.stroke();
		ctx.closePath();
	};

	const getFocusedVertex = (mx = 0, my = 0) => {
		let focus: any;
		const s = buffer.width / config.baseCanvasWidth;
		vertices.forEach((vertex, idx) => {
			vertex = mul(vertex, s);
			if (mx != null && my != null) {
				const distance = Math.sqrt(
					Math.pow(mx - vertex.x, 2) + Math.pow(my - vertex.y, 2)
				);
				if (
					distance <= config.vertexRadius * config.focusFactor &&
					(!focus?.vertex || distance < focus.distance)
				) {
					focus = {index: idx, distance};
				}
			}
		});
		return focus;
	};

	const getFocusedSegmentVertex = (mx: number = 0, my: number = 0) => {
		let focus: any;
		const s = buffer.width / config.baseCanvasWidth;
		segments.forEach((segment, idx) => {
			segment.forEach((vertex: any, _idx: any) => {
				vertex = mul(vertex, s);
				if (mx != null && my != null) {
					const distance = Math.sqrt(
						Math.pow(mx - vertex.x, 2) + Math.pow(my - vertex.y, 2)
					);
					if (
						distance <= config.vertexRadius * config.focusFactor &&
						(!focus?.vertex || distance < focus.distance)
					) {
						focus = {segment: idx, index: _idx, distance};
					}
				}
			});
		});
		return focus;
	};

	const updateCurve = () => {
		const result = kochanek_bartels_curve(config.bezierT, vertices, 0, 0, 0);
		curve = result.curve;
		segments = result.segments;
		value = segments;
	};

	const baseShape = () => {
		if (!states[currentState]?.isBaseState) {
			vertices = [];
			for (let i = 0; i < config.initialVertices; ++i) {
				vertices.push({
					x: Math.cos(((2 * Math.PI) / config.initialVertices) * i) * config.baseRadius,
					y: Math.sin(((2 * Math.PI) / config.initialVertices) * i) * config.baseRadius,
				});
			}
			updateCurve();
			pushState(true);
		}
	};

	const resetShape = () => {
		baseShape();
		update(UpdateType.Reset);
	};

	const pushState = (isBaseState: any = undefined) => {
		const data = deepCopy(vertices);
		data.isBaseState = isBaseState;
		states.splice(++currentState, states.length - currentState, data);
		const overflow = states.length - config.maxStatesCount;
		if (overflow > 0) {
			states.splice(0, overflow);
			currentState -= overflow;
		}
	};

	function setState(state: number = 0) {
		if (state >= 0 && state < states.length) {
			vertices = deepCopy(states[state]);
			currentState = state;
			updateCurve();
			update(UpdateType.StateChange);
		}
	}

	function onMouseUp({offsetX: mx, offsetY: my}: MouseEvent) {
			if (selectedVertex) {
				selectedVertex = null;
				update(UpdateType.MouseReleased, mx, my);
				pushState();
			}
		}

	onMount(() => {
		baseShape();
		resize();
		window.addEventListener('resize', () => resize());
	});


</script>

<!-- svelte-ignore a11y-autofocus -->
<div>
<BlockTitle {info} {show_label}>{label}</BlockTitle>
	<canvas
		bind:this={canvas}
		on:mousedown={onMouseDown}
		on:mouseup={onMouseUp}
		on:mousemove={onMouseMoved}
		on:contextmenu={event => event.preventDefault()}
		>
	</canvas>
	<div class="actions">
		<input
			class="button"
			on:click="{() => setState(currentState - 1)}"
			style="
              --image: url({undoWhite});
              --hover-image: url({undoBlack});
            "
			type="button"
		/>
		<input
			class="button"
				on:click="{() => setState(currentState - 1)}"
			style="
              --image: url({undoWhite});
              --hover-image: url({undoBlack});
              transform: scaleX(-1);
            "
			type="button"
		/>
		<input
			class="button"
			on:click="{resetShape}"
			style="
              --image: url({reloadWhite});
              --hover-image:  url({reloadBlack});
            "
			type="button"
		/>
	</div>
</div>

<style>
	canvas {
		width: 100%;
		height: 100%;
	}

	label {
		display: block;
		width: 100%;
	}

 .actions {
  bottom: 10px;
  display: flex;
  flex-direction: row;
  position: absolute;
  right: 10px;
}
 .actions > .button {
  background-image: var(--image);
  background-color: transparent;
  background-size: 80%;
  background-position: center;
  background-repeat: no-repeat;
  border-radius: 50%;
  border-style: none;
  cursor: pointer;
  height: 30px;
  outline-style: none;
  width: 30px;
}
 .actions > .button:hover {
  background-image: var(--hover-image);
  background-color: white;
}
</style>
