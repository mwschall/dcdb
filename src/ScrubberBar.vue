<template>
<div
  class="scrubber"
  v-touch:tap="handleNav"
  v-touch:pan="handleHover"
  v-touch:panend="handleNav"
  v-touch:press="handleHover"
  @mousedown="handleHover"
  @mouseover="handleHover"
  @mousemove="handleHover"
  @mouseout="handleHover"
  >
  <div class="dot" v-for="n in numDots" :key="n">•</div>
  <div class="cursor" :style="cursorStyle">•</div>
  <div class="tooltip" :style="tooltipStyle" v-show="hoverPage">
    <div class="content">{{ hoverPage }}</div>
  </div>
</div>
</template>

<script>
import _ from 'lodash'

export default {
  name: 'scrubber-bar',
  props: {
    currPage: {
      type: Number,
      required: true,
    },
    totalPages: {
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
      cursorPage: this.currPage,
      hoverPage: undefined,
      elWidth: 1,
      dotWidth: 1,
    }
  },
  computed: {
    numDots () {
      return Math.min(this.totalPages, Math.floor(this.elWidth / this.dotWidth))
    },
    cursorStyle () {
      return {
        left: this.getPos(this.cursorPage, this.totalPages),
      }
    },
    tooltipStyle () {
      return {
        left: this.getPos(this.hoverPage, this.totalPages),
      }
    },
  },
  methods: {
    getPos (num, total) {
      return `${100 * (((2 * (num - 1)) + 1) / (2 * total))}%`
    },
    getPage (event) {
      const pageX = event.center ? event.center.x : event.pageX
      const bcr = this.$el.getBoundingClientRect()
      const hoverX = pageX - window.scrollX - bcr.left
      const page = Math.ceil(this.totalPages * (hoverX / bcr.width))
      return _.clamp(page, 1, this.totalPages)
    },
    computeWidths () {
      const wcs = window.getComputedStyle(this.$el)
      this.elWidth = parseInt(wcs.width, 10)
      this.dotWidth = parseInt(wcs.fontSize, 10) * this.dotSpacingFactor
    },
    handleHover (event) {
      (event.srcEvent || event).stopPropagation()

      const etype = event.type
      if (etype === 'mouseout') {
        this.hoverPage = undefined
      } else {
        this.hoverPage = this.getPage(event)

        // cursor should track the user's mouse/finger when dragging
        if (etype === 'press' || etype === 'pan') {
          this.cursorPage = this.hoverPage
        }
      }
    },
    handleNav (event) {
      (event.srcEvent || event).stopPropagation()
      // kill ephemeral mouse events post-'tap'
      event.preventDefault()

      const page = this.getPage(event)
      if (page) {
        this.$emit('nav', page)
      }

      const etype = event.type
      if (etype === 'tap' || etype === 'panend') {
        this.hoverPage = undefined
      }
    },
  },
  watch: {
    currPage (newPage) {
      this.cursorPage = newPage
    },
  },
  mounted () {
    this.$nextTick(this.computeWidths)
    window.addEventListener('resize', this.computeWidths)
  },
  beforeDestroy () {
    window.removeEventListener('resize', this.computeWidths)
  },
}
</script>

<style lang="stylus">
$scrubberSize = 2rem
$dotSize = 1rem
$dotPositioning = 0.25 * $scrubberSize
$cursorSize = 1rem

$altColor = #ddd
$contrastColor = rgba(25, 25, 25, 0.75)

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
  height $scrubberSize

  .dot
  .cursor
    box-sizing border-box
    text-align center

  .dot
    line-height $dotSize
    width 100%
    padding-top $dotPositioning
    text-shadow -1px 0 $altColor, 0 1px $altColor, 1px 0 $altColor, 0 -1px $altColor

  .cursor
    color $altColor
    background-color $contrastColor
    border-radius 0.1875rem
    box-shadow 0 0 0 0.0625rem $altColor
    width $cursorSize
    height $cursorSize
    margin-left -0.5 * @width
    margin-top -0.5 * @height
    line-height @height
    position absolute
    top $dotPositioning + (0.5 * $dotSize)

  .tooltip
    position absolute
    top 0
    margin-top -1.8rem

    .content
      color $altColor
      background-color $contrastColor
      border-radius 0.125rem
      position relative
      width 2rem
      margin-left -1rem
      margin-bottom .5rem
      padding 0.1rem 0 0.1rem
      text-align center

      &:before
        content ''
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
        border-top-color $contrastColor
</style>
