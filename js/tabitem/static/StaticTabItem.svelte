<script lang="ts">
	import type { Gradio, SelectData } from "@gradio/utils";
	import TabItem from "./TabItem.svelte";

	export let elem_id = "";
	export let elem_classes: string[] = [];
	export let label: string;
	export let id: string | number;
	export let gradio: Gradio<{
		select: SelectData;
	}>;
</script>

<TabItem
	{elem_id}
	{elem_classes}
	name={label}
	{id}
	on:select={({ detail }) => gradio.dispatch("select", detail)}
>
	<slot />
</TabItem>
