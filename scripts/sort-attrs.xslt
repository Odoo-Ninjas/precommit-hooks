<?xml version="1.0"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
  <!-- Specify the output method and indicate which elements should retain CDATA -->
  <xsl:output method="xml" indent="yes" cdata-section-elements="text"/>

  <!-- Template to match any element -->
  <xsl:template match="*">
    <xsl:copy>
      <!-- Sort and copy attributes -->
      <xsl:for-each select="@*">
        <!-- Assign custom sort priority: id=1, name=2, record=3, rest=9 -->
        <xsl:sort select="
          concat(
            substring('1', 1 div (name()='id')),
            substring('2', 1 div (name()='name')),
            substring('3', 1 div (name()='record')),
            substring('9', 1 div (not(name()='id' or name()='name' or name()='record')))
          )
        " data-type="number"/>
        <xsl:sort select="name()" data-type="text"/>
        <xsl:copy/>
      </xsl:for-each>

      <!-- Copy all child nodes -->
      <xsl:apply-templates select="node()"/>
    </xsl:copy>
  </xsl:template>

  <!-- Identity template for non-element content -->
  <xsl:template match="@*|text()|comment()|processing-instruction()">
    <xsl:copy/>
  </xsl:template>
</xsl:stylesheet>