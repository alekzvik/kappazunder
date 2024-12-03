<script lang="ts">
  import Map from "./lib/Map.svelte";
  import PhotoViewer from "./lib/PhotoViewer.svelte";
  import PointClouds from "./lib/PointClouds.svelte";
  import { Position } from "./lib/state.svelte";
  import "@photo-sphere-viewer/core/index.css";

  const position = new Position();
</script>

<main>
  <Map {position} />
  <!-- <PhotoViewer {position} /> -->
   <!-- <PointClouds /> -->
</main>

<style>
  main {
    display: flex;
    flex-direction: column;
    height: 98vh;
    margin: 1vh 0.5vw;
  }

  :global(body) {
    margin: 0;
  }

  :global(main > *) {
    flex: 1; /* Make both Map and StreetView components flex equally */
    width: 100%; /* Ensure full width */
  }
</style>
