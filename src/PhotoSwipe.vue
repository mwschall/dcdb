<template lang="pug">
div.pswp(tabindex='-1', role='dialog', ariaHidden='true')
  div.pswp__bg
  div.pswp__scroll-wrap
    div.pswp__container(@click='handleNav')
      div.pswp__item
      div.pswp__item
      div.pswp__item
    div.pswp__ui.pswp__ui--hidden
      div.pswp__top-bar
        button.pswp__button.pswp__button--close(title='Close (Esc)')
        button.pswp__button.pswp__button--fs(title='Toggle fullscreen')
        button.pswp__button.pswp__button--zoom(title='Zoom in/out')
        div.pswp__info(v-touch:tap='toggleTitle')
          div.pswp__title {{ title }}
          div.pswp__synopsis(v-if='info' v-show='showInfo')
            div(v-if='featuring')
              h4 On This Page
              div(v-html='featuring')
            div(v-if='synopsis')
              h4 Synopsis
              p {{ synopsis }}
        div.pswp__preloader
          div.pswp__preloader__icn
            div.pswp__preloader__cut
              div.pswp__preloader__donut
      div.pswp__button.pswp__button--arrow--left(title='Previous (arrow left)')
      div.pswp__button.pswp__button--arrow--right(title='Next (arrow right)')
      div.pswp__extra
        slot(name='additional-ui')
</template>

<script>
import _ from 'lodash'
import PhotoSwipe from 'photoswipe'
import PhotoSwipeUIDefault from 'photoswipe/dist/photoswipe-ui-default'

function getPswpOptions () {
  return {
    history: false,
    loop: false,
    preload: [1, 3],

    // UI Options
    mainClass: 'pswp--minimal--dark',
    barsSize: { top: 0, bottom: 0 },
    captionEl: false,
    counterEl: false,
    shareEl: false,
    bgOpacity: 1,
    closeElClasses: ['item', 'zoom-wrap', 'ui', 'top-bar'],
    clickToCloseNonZoomable: false,
    closeOnScroll: false,
    tapToClose: false,
    tapToToggleControls: true,
  }
}

export default {
  name: 'viewport',
  props: {
    index: {
      type: Number,
      required: true,
    },
    items: {
      type: Array,
      required: true,
    },
    loaded: {
      type: Boolean,
      required: true,
    },
    thread: {
      type: Object,
      required: true,
    },
  },
  data () {
    return {
      gallery: undefined,
      showInfo: false,
    }
  },
  computed: {
    title () {
      return this.items[this.index].title || this.thread.name
    },
    synopsis () {
      return this.items[this.index].synopsis || this.thread.synopsis
    },
    featuring () {
      const types = _.groupBy(this.items[this.index].appearances, 'type')
      const html = []
      if (types.S) {
        html.push(`Visible: ${types.S.map(a => a.persona.name).join(', ')}`)
      }
      if (types.O || types.M) {
        html.push(`Other: ${_.filter(_.concat(types.O, types.M)).map(a => a.persona.name).join(', ')}`)
      }
      return html.join('<br>')
    },
    info () {
      return this.synopsis || this.featuring
    },
  },
  mounted () {
    this.init()
  },
  beforeDestroy () {
    if (this.gallery) {
      this.gallery.destroy()
    }
  },
  watch: {
    index (newIndex) {
      if (this.gallery && this.loaded) {
        this.gallery.goTo(newIndex)
      }
    },
    loaded (isLoaded) {
      if (this.gallery && isLoaded) {
        this.gallery.goTo(this.index)
      }
    },
    thread () {
      const pswp = this.gallery
      pswp.invalidateCurrItems()
      pswp.updateSize(true)
      pswp.ui.update()
    },
  },
  methods: {
    toggleTitle () {
      if (this.info) {
        this.showInfo = !this.showInfo
      }
    },
    init () {
      if (this.gallery || !this.$el) {
        return
      }

      this.gallery = new PhotoSwipe(
        this.$el,
        PhotoSwipeUIDefault,
        this.items,
        Object.assign(getPswpOptions(), {
          index: this.index,
        }),
      )

      this.gallery.listen('beforeChange', () => {
        const index = this.gallery.getCurrentIndex()
        this.$emit('nav', index)
      })

      this.gallery.listen('afterChange', () => {
        const item = this.gallery.currItem
        if (item.alt) {
          const img = document.querySelector(`.pswp__img[src='${item.src}']`)
          img.setAttribute('title', item.alt)
        }
      })

      this.gallery.listen('close', () => {
        this.$emit('close')
      })

      this.gallery.init()
    },
    handleNav (event) {
      const link = event.target.getAttribute('href')
      if (link) {
        this.$emit('nav', link)
        event.stopPropagation()
        event.preventDefault()
      }
    },
  },
}
</script>

<style lang="stylus">
@import "~photoswipe/dist/photoswipe.css";
@import "~photoswipe/dist/default-skin/default-skin.css";

$barSize = 44px
$titlePad = 10/16rem
$synopsisFullWidth = 450px

$fontColor = #fff
$altColor = #000
$contrastColor = rgba(25, 25, 25, 0.85)

.no-script .pswp__img
  touch-action none
  max-width 100%
  max-height 100%
  margin auto
  position absolute
  left 0
  right 0
  top 0
  bottom 0

.pswp__info
  color $fontColor
  cursor default
  user-select none
  font-size 1rem
  float left
  position relative

  .pswp__title
    line-height $barSize
    padding 0 $titlePad

  .pswp__synopsis
    width $synopsisFullWidth
    position absolute
    left .5 * $titlePad
    top (.5 * $barSize) + (.5 * @font-size * 16px) + (@left * 16px)

    p
      background-color $contrastColor
      border-radius .5 * $titlePad
      font-size (12/16rem)
      max-width 300px
      box-sizing border-box
      margin 0
      padding .5 * $titlePad
      position relative
      float left

      @media (min-width: 992px)
        max-width $synopsisFullWidth
</style>
