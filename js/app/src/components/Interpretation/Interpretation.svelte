<script lang="ts">
	import type { ComponentType } from "svelte";
	import type { SvelteComponent } from "svelte";
	import { component_map } from "./directory";

	export let component: keyof typeof component_map;
	export let component_props: Record<string, any>;
	export let value: any;

	$: _component = component_map[component] as ComponentType<SvelteComponent>;
</script>

{#if value}
	<svelte:component
		this={_component}
		{...component_props}
		original={value.original}
		interpretation={value.interpretation}
	/>
{/if}
