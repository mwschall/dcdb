<template lang="pug">
div.scrubber(
  v-touch:tap='handleNav',
  v-touch:pan='handleHover',
  v-touch:panend='handleNav',
  v-touch:press='handleHover',
  @mousedown='handleHover',
  @mouseover='handleHover',
  @mousemove='handleHover',
  @mouseout='handleHover',
  )
  div.dot(v-for='n in numDots', :key='n') {{ dotContent }}
  div.cursor(:style='cursorStyle', v-show='cursorIndex < total')
    div.content {{ cursorContent }}
  div.tooltip(:style='tooltipStyle', v-show='hoverIndex >= 0')
    div.content {{ tooltipContent }}
</template>

<script>
import _ from 'lodash'

const DOT = '•'

export default {
  name: 'scrubber-bar',
  props: {
    cursor: {
      type: String,
      default: 'dot',
      validator (value) {
        return _.includes(['num', 'dot'], value)
      },
    },
    items: {
      type: Array,
      required: true,
    },
    index: {
      type: Number,
      required: true,
    },
    total: {
      type: Number,
      required: true,
      validator (value) {
        return value >= 0
      },
    },
    dotContent: {
      type: String,
      default: DOT,
    },
    dotSpacingFactor: {
      type: Number,
      default: 0.8,
    },
  },
  data () {
    return {
      cursorIndex: this.index,
      hoverIndex: undefined,
      elWidth: 1,
      dotWidth: 1,
    }
  },
  computed: {
    numDots () {
      return Math.min(this.total, Math.floor(this.elWidth / this.dotWidth)) || 1
    },
    cursorStyle () {
      return {
        left: this.getPos(this.cursorIndex),
      }
    },
    cursorContent () {
      if (this.cursor === 'num') {
        return this.getLabel(this.cursorIndex)
      }
      return this.dotContent
    },
    tooltipStyle () {
      return {
        left: this.getPos(this.hoverIndex),
      }
    },
    tooltipContent () {
      return this.getLabel(this.hoverIndex)
    },
  },
  mounted () {
    window.addEventListener('resize', this.computeWidths)
    this.init()
  },
  beforeDestroy () {
    window.removeEventListener('resize', this.computeWidths)
  },
  methods: {
    init () {
      this.computeWidths()
      if (!this.elWidth || !this.dotWidth) {
        _.delay(this.init, 50)
      }
    },
    getLabel (index) {
      const item = this.items[index]
      if (item && typeof item.number !== 'undefined') {
        return item.number
      // } else if ('has cover') {
      //   // do something special
      }
      return index + 1
    },
    getPos (num) {
      return `${100 * (((2 * num) + 1) / (2 * this.total))}%`
    },
    getIndex (event) {
      const pageX = event.center ? event.center.x : event.pageX
      const bcr = this.$el.getBoundingClientRect()
      const hoverX = pageX - window.scrollX - bcr.left
      const index = Math.floor(this.total * (hoverX / bcr.width))
      return _.clamp(index, 0, this.total - 1)
    },
    computeWidths () {
      const wcs = window.getComputedStyle(this.$el)
      this.elWidth = parseInt(wcs.width, 10)
      this.dotWidth = parseInt(wcs.fontSize, 10) * this.dotSpacingFactor
    },
    handleHover (event) {
      const etype = event.type

      // allow these through for idle tracking but stop everything else
      if (!_.includes(['mousemove', 'mouseover', 'mouseout'], etype)) {
        (event.srcEvent || event).stopPropagation()
      }

      if (etype === 'mouseout') {
        this.hoverIndex = undefined
      } else {
        this.hoverIndex = this.getIndex(event)

        // cursor should track the user's mouse/finger when dragging
        if (etype === 'press' || etype === 'pan') {
          this.cursorIndex = this.hoverIndex
        }
      }
    },
    handleNav (event) {
      (event.srcEvent || event).stopPropagation()
      // kill ephemeral mouse events post-'tap'
      event.preventDefault()

      this.$emit('nav', this.getIndex(event))

      const etype = event.type
      if (etype === 'tap' || etype === 'panend') {
        this.hoverIndex = undefined
      }
    },
  },
  watch: {
    index (newIndex) {
      this.cursorIndex = newIndex
    },
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
      padding 0 .1875rem

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
