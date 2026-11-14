# 258 Web Co. campaign collateral

The HTML files are editable masters. They use the repository’s local Inter font and the 258 Web Co. header mark. The [studio guide](../04-studio-identity.md) records the palette and usage. The [copy bank](../05-launch-and-marketing.md) includes the share-card caption and alternative text.

- Use the **one-sheet PDF** for introductions by email or print it on US Letter. Its call to action asks the recipient to reply to the sender.
- Use the **share-card PNG** with a useful caption and an approved destination. The text on the graphic is also available in the HTML and copy bank.

To regenerate the supplied exports with WeasyPrint and Poppler, run from this folder:

```sh
weasyprint -q --allowed-protocols file --pdf-variant pdf/ua-1 258webco-one-sheet.html 258webco-one-sheet.pdf
work_dir="$(mktemp -d)"
weasyprint -q --allowed-protocols file 258webco-share.html "$work_dir/share.pdf" &&
  pdftoppm -f 1 -l 1 -singlefile -r 96 -png "$work_dir/share.pdf" 258webco-share
rm -f "$work_dir/share.pdf"
rmdir "$work_dir"
```

Check the one-sheet is one tagged Letter page with selectable text. Check the share image is 1200 × 630. Inspect both at their intended size after changing copy or typography.
