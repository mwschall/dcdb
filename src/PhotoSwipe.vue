<template lang="pug">
div.pswp(tabindex='-1', role='dialog', ariaHidden='true', ref='pswp')
  div.pswp__bg
  div.pswp__scroll-wrap
    div.pswp__container
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
          div.pswp__synopsis(
            v-if='synopsis'
            v-show='showSynopsis'
            ) {{ synopsis }}
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
    timeToIdle: 0,
  }
}

export default {
  name: 'viewport',
  props: ['items', 'loaded', 'index', 'title', 'synopsis'],
  data () {
    return {
      gallery: undefined,
      showSynopsis: false,
    }
  },
  methods: {
    toggleTitle () {
      if (this.synopsis) {
        this.showSynopsis = !this.showSynopsis
      }
    },
    open () {
      if (this.gallery || !this.$el) {
        return
      }

      this.gallery = new PhotoSwipe(
        this.$refs.pswp,
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
  },
  watch: {
    index (newIndex) {
      if (this.gallery) {
        this.gallery.goTo(newIndex)
      }
    },
    loaded () {
      const pswp = this.gallery
      pswp.invalidateCurrItems()
      pswp.updateSize(true)
      pswp.ui.update()
    },
  },
  mounted () {
    this.open()
  },
  beforeDestroy () {
    if (this.gallery) {
      this.gallery.close()
    }
  },
}
</script>

<style lang="stylus">
@import "~photoswipe/dist/photoswipe.css";
@import "~photoswipe/dist/default-skin/default-skin.css";

$barSize = 44px
$titlePad = 10/16rem

$fontColor = #fff
$altColor = #000
$contrastColor = rgba(25, 25, 25, 0.85)

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
    background-color $contrastColor
    border-radius 0.5 * $titlePad
    box-sizing border-box
    max-width 300px
    padding 0.5 * $titlePad
    font-size (12/16rem)
    position absolute
    left 0.5 * $titlePad
    top (0.5 * $barSize) + (0.5 * @font-size * 16px) + (@left * 16px)

    @media (min-width: 992px)
      max-width 450px
</style>
