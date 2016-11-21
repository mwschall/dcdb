<template>
  <div class="spinner" :class="{ show: show }">Loading...</div>
</template>

<script>
export default {
  props: ['show'],
}
</script>

<style lang="stylus">
// Original CSS from https://projects.lukehaas.me/css-loaders/

$barcolor = #fff
$duration = 0.8s
$scale = .5rem

.spinner
  visibility hidden
  opacity 0
  color $barcolor
  text-indent -9999rem

  &
  &:before
  &:after
    background $barcolor
    width $scale
    height 4 * $scale
    animation spinner $duration infinite ease-in-out
    animation-play-state paused
  &:before
    animation-delay -0.32 * $duration
  &
    animation-delay -0.16 * $duration
  &.show
    visibility visible
    opacity 0.9
    &
    &:before
    &:after
      animation-play-state running

  position absolute
  top 50%
  left 50%
  margin -2 * $scale 0 0 -0.5 * $scale
  &:before
  &:after
    content ''
    position absolute
    top 0
  &:before
    left -1.5 * $scale
  &:after
    left 1.5 * $scale

@keyframes spinner
  0%
  80%
  100%
    box-shadow 0 0
    height 4 * $scale
  40%
    box-shadow 0 -2 * $scale
    height 5 * $scale
</style>
