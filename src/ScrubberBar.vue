<template>
<div
  class="scrubber"
  @click.stop="handleNav"
  @mouseover="handleHover"
  @mousemove="handleHover"
  @mouseout="hoverPage = undefined"
  >
  <div class="dot" v-for="n in numDots" :key="n">•</div>
  <div
    class="tooltip"
    v-show="hoverPage"
    :style="tooltipStyle"
    >
    <div class="content">{{ hoverPage }}</div>
  </div>
</div>
</template>

<script>
export default {
  name: 'scrubber-bar',
  props: {
    numPages: {
      type: Number,
      required: true,
      validator (value) {
        return value > 0
      },
    },
    dotSpacingFactor: {
      type: Number,
      default: 0.8,
    },
  },
  data () {
    return {
      hoverPage: undefined,
      elWidth: 1,
      dotWidth: 1,
    }
  },
  computed: {
    numDots () {
      return Math.min(this.numPages, Math.floor(this.elWidth / this.dotWidth))
    },
    hoverFraction () {
      return ((2 * (this.hoverPage - 1)) + 1) / (2 * this.numPages)
    },
    tooltipStyle () {
      return {
        left: `${100 * this.hoverFraction}%`,
      }
    },
  },
  methods: {
    computeWidths () {
      const wcs = window.getComputedStyle(this.$el)
      this.elWidth = parseInt(wcs.width, 10)
      this.dotWidth = parseInt(wcs.fontSize, 10) * this.dotSpacingFactor
    },
    handleHover (event) {
      const bcr = this.$el.getBoundingClientRect()
      const hoverX = event.pageX - window.scrollX - bcr.left
      this.hoverPage = Math.ceil(this.numPages * (hoverX / bcr.width)) || 1
    },
    handleNav () {
      this.$emit('nav', this.hoverPage)
    },
  },
  mounted () {
    this.computeWidths()
    window.addEventListener('resize', this.computeWidths)
  },
  beforeDestroy () {
    window.removeEventListener('resize', this.computeWidths)
  },
}
</script>

<style lang="stylus">
.scrubber
  background-color rgba(25, 25, 25, 0.4)
  border-radius .25rem .25rem 0 0
  cursor pointer

  display flex
  flex-flow row nowrap

  position absolute
  bottom 0
  right 2rem
  left 2rem
  height 2rem

  .dot
    box-sizing border-box
    text-align center
    width 100%
    padding-top 0.3rem
    text-shadow -1px 0 #ddd, 0 1px #ddd, 1px 0 #ddd, 0 -1px #ddd

  .tooltip
    position absolute
    top 0
    margin-top -1.6rem

    .content
      background-color green
      position relative
      width 2rem
      margin-left -1rem
      margin-bottom .5rem
      text-align center

      &:before
        content ""
        display block
        position absolute
        width 0
        height 0
        border-color transparent
        border-width .5rem .5rem 0
        border-style solid

      &:before
        top 100%
        left 50%
        margin-left -.5rem
        border-top-color green
</style>
