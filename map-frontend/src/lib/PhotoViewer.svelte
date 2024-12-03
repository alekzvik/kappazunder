<script lang="ts">
    import { Viewer, events } from "@photo-sphere-viewer/core";
    import { CubemapAdapter } from "@photo-sphere-viewer/cubemap-adapter";

    import { onMount } from "svelte";
    import { Position } from "./state.svelte";

    interface Props {
        position: Position;
    }

    let { position }: Props = $props();

    const POSITION_UPDATE_TIMEOUT = 0;

    let container: HTMLElement;
    let timeoutId: ReturnType<typeof setTimeout>;

    onMount(() => {
        const viewer = new Viewer({
            container: container,
            adapter: CubemapAdapter,
            panorama: {
                type: "separate",
                paths: {
                    left: "/images/left.jpg",
                    front: "/images/front.jpg",
                    right: "/images/right.jpg",
                    back: "/images/back.jpg",
                    top: "/images/top.jpg",
                    bottom: "/images/bottom.jpg",
                },
                flipTopBottom: true,
            },
            defaultYaw: position.bearing,
            defaultPitch: position.pitch,
        });
        function updatePosition({
            position: viewerPosition,
        }: events.PositionUpdatedEvent) {
            if (timeoutId) clearTimeout(timeoutId);
            timeoutId = setTimeout(() => {
                position.updateOrientation(
                    viewerPosition.yaw,
                    viewerPosition.pitch,
                );
            }, POSITION_UPDATE_TIMEOUT);
        }
        viewer.addEventListener("position-updated", updatePosition);

        return () => {
            viewer.removeEventListener("position-updated", updatePosition);
            viewer.destroy();
        };
    });
</script>

<div id="viewer" bind:this={container}></div>

<style>
    #viewer {
        width: 100%;
        height: 100%;
    }
</style>
