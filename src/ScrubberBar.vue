<template lang="pug">
div.scrubber(
  v-touch:tap="handleNav",
  v-touch:pan="handleHover",
  v-touch:panend="handleNav",
  v-touch:press="handleHover",
  @mousedown="handleHover",
  @mouseover="handleHover",
  @mousemove="handleHover",
  @mouseout="handleHover",
  )
  div.dot(v-for="n in numDots", :key="n") {{ dotContent }}
  div.cursor(:style="cursorStyle")
    div.content {{ cursorContent }}
  div.tooltip(:style="tooltipStyle", v-show="hoverPage")
    div.content {{ hoverPage }}
</template>

<script>
import _ from 'lodash'

const DOT = '•'

export default {
  name: 'scrubber-bar',
  props: {
    cursor: {
      type: String,
      default: 'num',
      validator (value) {
        return _.includes(['num', 'dot'], value)
      },
    },
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
      dotContent: DOT,
    }
  },
  computed: {
    numDots () {
      return Math.min(this.totalPages, Math.floor(this.elWidth / this.dotWidth))
    },
    cursorContent () {
      return this.cursor === 'num' ? this.cursorPage : this.dotContent
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
$tooltipSize = 1.25rem
$arrowSize = 9/16rem

$altColor = #ddd
$contrastColor = rgba(25, 25, 25, 0.85)

.scrubber
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
  .tooltip
    box-sizing border-box
    text-align center

  .dot
    line-height $dotSize
    width 100%
    padding-top $dotPositioning
    text-shadow -1px 0 $altColor, 0 1px $altColor, 1px 0 $altColor, 0 -1px $altColor

  .cursor
  .tooltip
    display flex
    justify-content center
    width 6 * $cursorSize
    margin-left -0.5 * @width
    position absolute

    .content
      flex min-content
      color $altColor
      background-color $contrastColor

  .cursor
    height $cursorSize
    margin-top -0.5 * @height
    line-height @height
    top $dotPositioning + (0.5 * $dotSize)

    .content
      min-width $cursorSize
      border-radius 0.1875rem
      box-shadow 0 0 0 0.0625rem $altColor
      padding 0 .1875rem


  .tooltip
    margin-top -($tooltipSize + $arrowSize)
    font-size $tooltipSize
    top 0

    .content
      min-width 1.5 * $tooltipSize
      border-radius 0.125rem
      position relative
      margin-bottom $arrowSize

      &:before
        content ''
        display block
        position absolute
        width 0
        height 0
        border-color transparent
        border-width $arrowSize $arrowSize 0
        border-style solid

      &:before
        top 100%
        left 50%
        margin-left -($arrowSize)
        border-top-color $contrastColor
</style>
