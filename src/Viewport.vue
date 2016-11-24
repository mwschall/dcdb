<template>
  <div
    class="viewport"
    v-touch:pinch="handleHammer"
    v-touch:pinchend="handleHammerEnd"
    >
    <img
      :src="src"
      :class="{ fit: fit }"
      :style="imgStyle"
      @load="handleLoad"
      @dragstart.prevent
      unselectable="on"
      draggable="false"
      ref="img"
      />
  </div>
</template>

<script>
// http://hammerjs.github.io/tips/#remove-tap-highlight-on-windows-phone
(function tapHighlightFix () {
  const meta = document.createElement('meta')
  meta.name = 'msapplication-tap-highlight'
  meta.content = 'no'
  document.getElementsByTagName('head')[0].appendChild(meta)
}())

function getWindowFit (img) {
  return Math.min(
    window.innerWidth / img.naturalWidth,
    window.innerHeight / img.naturalHeight,
  )
}

function hotFreshValuesFor (instance) {
  const img = instance.$refs.img
  return {
    fit: true,
    scale: img ? getWindowFit(img) : 1,
    zoom: 1,
    translateX: 0,
    translateY: 0,
    deltaX: 0,
    deltaY: 0,
  }
}

export default {
  name: 'viewport',
  props: ['src'],
  data () {
    return Object.assign(hotFreshValuesFor(this), {
      // img will already be loaded, yes?
      free: true,
    })
  },
  computed: {
    imgStyle () {
      if (this.fit) {
        return {}
      }

      const img = this.$refs.img
      const ww = window.innerWidth
      const wh = window.innerHeight
      const x = (ww / 2) + this.translateX + this.deltaX
      const y = (wh / 2) + this.translateY + this.deltaY
      const w = this.zoom * this.scale * img.naturalWidth
      const h = this.zoom * this.scale * img.naturalHeight
      return {
        left: `${100 * (x / ww)}%`,
        top: `${100 * (y / wh)}%`,
        marginLeft: `-${w / 2}px`,
        marginTop: `-${h / 2}px`,
        width: `${w}px`,
        height: `${h}px`,
      }
    },
  },
  methods: {
    handleLoad () {
      Object.assign(this.$data, hotFreshValuesFor(this))
      this.free = true
    },
    handleHammer (event) {
      if (this.free) {
        this.fit = false
        this.zoom = event.scale
        this.deltaX = event.deltaX
        this.deltaY = event.deltaY
      }
    },
    handleHammerEnd () {
      if (this.free) {
        this.scale *= this.zoom
        this.zoom = 1
        this.translateX += this.deltaX
        this.translateY += this.deltaY
        this.deltaX = this.deltaY = 0
      }
    },
    handleResize () {
      if (!this.moved) {
        this.scale = getWindowFit(this.$refs.img)
      } else {
        // TODO: consider rescaling based on new width/height ratio vs. old
      }
    },
  },
  watch: {
    src () {
      // no moving while image is loading
      this.free = false
    },
  },
  mounted () {
    window.addEventListener('resize', this.handleResize)
  },
  beforeDestroy () {
    window.removeEventListener('resize', this.handleResize)
  },
}
</script>

<style lang="stylus">
.viewport
  background #000
  width 100%
  height 100%
  margin 0

  user-select none

  img
    position absolute
    &.fit
      top 0
      left 0
      bottom 0
      right 0
      margin auto
      max-height 100%
      max-width 100%
</style>
